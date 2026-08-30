"""
FortiGate REST API client — multi-device registry.
Wraps httpx with async methods for all the operations the MCP tools need.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel


# ─── Config models ─────────────────────────────────────────────────────────────

class FortiGateDevice(BaseModel):
    """Connection configuration for one FortiGate device."""

    host: str  # e.g. "https://10.0.0.1"
    api_token: str
    vdom: str = "root"
    verify_ssl: bool = True
    name: str = "default"  # registry key

    @property
    def base_url(self) -> str:
        return f"{self.host.rstrip('/')}/api/v2"


class MultiFortiGateRegistry:
    """
    Registry of multiple FortiGate devices.
    Default device comes from env vars (FORTIGATE_* vars).
    Additional devices are loaded from config/devices.yaml.
    """

    DEFAULT_NAME = "default"

    def __init__(self) -> None:
        self._devices: dict[str, FortiGateDevice] = {}
        self._clients: dict[str, FortiGateClient] = {}
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def device_names(self) -> list[str]:
        """Return all registered device names."""
        return list(self._devices.keys())

    def default_device(self) -> FortiGateDevice:
        """Return the default device (first registered)."""
        return self._devices[self.DEFAULT_NAME]

    def get_device(self, name: str | None) -> FortiGateDevice:
        """Resolve a device by name, defaulting to the default device."""
        if not name or name == self.DEFAULT_NAME:
            return self.default_device()
        if name not in self._devices:
            raise KeyError(f"Device '{name}' not found. Available: {self.device_names()}")
        return self._devices[name]

    def get_client(self, name: str | None = None) -> FortiGateClient:
        """Get (or create) an HTTP client for the named device."""
        dev = self.get_device(name)
        if dev.name not in self._clients:
            self._clients[dev.name] = FortiGateClient(dev)
        return self._clients[dev.name]

    async def close_all(self) -> None:
        """Close all open HTTP clients."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

    # ── Private ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        # 1. Load default device from environment variables
        default = FortiGateDevice(
            name=self.DEFAULT_NAME,
            host=os.getenv("FORTIGATE_HOST", "https://localhost"),
            api_token=os.getenv("FORTIGATE_API_TOKEN", ""),
            vdom=os.getenv("FORTIGATE_VDOM", "root"),
            verify_ssl=os.getenv("FORTIGATE_INSECURE", "false").lower() != "true",
        )
        self._devices[self.DEFAULT_NAME] = default

        # 2. Load additional devices from config/devices.yaml
        config_path = Path(__file__).parent.parent.parent / "config" / "devices.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                raw = yaml.safe_load(f) or {}
            for entry in raw.get("devices", []) or []:
                dev = FortiGateDevice(**entry)
                self._devices[dev.name] = dev


# ─── Single-device client (kept for direct use) ────────────────────────────────

class FortiGateClient:
    """Async HTTP client for FortiGate REST API (v2)."""

    def __init__(self, config: FortiGateDevice) -> None:
        self.cfg = config
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_token}",
                "Content-Type": "application/json",
            },
            verify=config.verify_ssl,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._http.aclose()

    # ── Firewall Objects ─────────────────────────────────────

    async def list_addresses(self) -> list[dict[str, Any]]:
        """Return all firewall addresses."""
        return await self._get("/cmdb/firewall/address", scope="vdom")

    async def create_address(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a firewall address object."""
        return await self._post("/cmdb/firewall/address", payload)

    async def update_address(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update an existing firewall address by name."""
        return await self._put(f"/cmdb/firewall/address/{name}", payload)

    async def delete_address(self, name: str) -> dict[str, Any]:
        """Delete a firewall address by name."""
        return await self._delete(f"/cmdb/firewall/address/{name}")

    async def list_address_groups(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/firewall/addrgrp", scope="vdom")

    async def list_services(self) -> list[dict[str, Any]]:
        """Return all firewall service (protocol) objects."""
        return await self._get("/cmdb/firewall.service/custom", scope="vdom")

    async def create_service(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post("/cmdb/firewall.service/custom", payload)

    async def delete_service(self, name: str) -> dict[str, Any]:
        return await self._delete(f"/cmdb/firewall.service/custom/{name}")

    # ── Policies ────────────────────────────────────────────

    async def list_policies(self) -> list[dict[str, Any]]:
        """Return all firewall policies."""
        return await self._get("/cmdb/firewall/policy", scope="vdom")

    async def create_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post("/cmdb/firewall/policy", payload)

    async def update_policy(self, policy_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._put(f"/cmdb/firewall/policy/{policy_id}", payload)

    async def delete_policy(self, policy_id: int) -> dict[str, Any]:
        return await self._delete(f"/cmdb/firewall/policy/{policy_id}")

    # ── NAT Policies ────────────────────────────────────────

    async def list_nat_policies(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/firewall/central-nat-map", scope="vdom")

    # ── VLAN / Interface ────────────────────────────────────

    async def list_interfaces(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/system/interface", scope="vdom")

    # ── Static Routes ──────────────────────────────────────

    async def list_routes(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/router/static", scope="vdom")

    # ── SSLVPN ─────────────────────────────────────────────

    async def list_sslvpn_settings(self) -> dict[str, Any]:
        """Return SSLVPN portal settings."""
        return await self._get("/cmdb/vpn.ssl/settings")

    async def list_sslvpn_users(self) -> list[dict[str, Any]]:
        """Return local SSL VPN users."""
        return await self._get("/cmdb/user/local", scope="vdom")

    async def list_sslvpn_groups(self) -> list[dict[str, Any]]:
        """Return SSL VPN user groups."""
        return await self._get("/cmdb/user/group", scope="vdom")

    async def list_sslvpn_connections(self) -> dict[str, Any]:
        """Return active SSLVPN connections."""
        return await self._get("/monitor/vpn/ssl")

    # ── IPSec VPN ─────────────────────────────────────────

    async def list_ipsec_phase1(self) -> list[dict[str, Any]]:
        """Return IPSec phase-1 (IKE) tunnel configurations."""
        return await self._get("/cmdb/vpn.ipsec/phase1-interface", scope="vdom")

    async def list_ipsec_phase2(self) -> list[dict[str, Any]]:
        """Return IPSec phase-2 (ESP) tunnel configurations."""
        return await self._get("/cmdb/vpn.ipsec/phase2-interface", scope="vdom")

    async def list_ipsec_connections(self) -> dict[str, Any]:
        """Return active IPSec VPN tunnel status."""
        return await self._get("/monitor/vpn/ipsec")

    # ── User / Authentication ─────────────────────────────

    async def list_users(self) -> list[dict[str, Any]]:
        """Return local user accounts."""
        return await self._get("/cmdb/user/local", scope="vdom")

    async def list_user_groups(self) -> list[dict[str, Any]]:
        """Return local user groups."""
        return await self._get("/cmdb/user/group", scope="vdom")

    async def list_firewall_authenticated_users(self) -> dict[str, Any]:
        """Return currently authenticated firewall users."""
        return await self._get("/monitor/user/firewall")

    # ── WiFi Controller (AP) ──────────────────────────────

    async def list_wifi_ap(self) -> list[dict[str, Any]]:
        """Return managed Access Points (AP) status."""
        return await self._get("/cmdb/wifi/ap", scope="vdom")

    async def list_wifi_client(self) -> dict[str, Any]:
        """Return connected WiFi clients."""
        return await self._get("/monitor/wifi/client")

    async def list_wifi_ssid(self) -> list[dict[str, Any]]:
        """Return SSID (WLAN) configurations."""
        return await self._get("/cmdb/wifi/ssid", scope="vdom")

    # ── Security Profiles ─────────────────────────────────

    async def list_antivirus_profile(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/antivirus/profile", scope="vdom")

    async def list_ips_profile(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/ips/sensor", scope="vdom")

    async def list_webfilter_profile(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/webfilter/profile", scope="vdom")

    async def list_application_list(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/application/list", scope="vdom")

    # ── DHCP ──────────────────────────────────────────────

    async def list_dhcp_server(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/system.dhcp/server", scope="vdom")

    async def list_dhcp_lease(self) -> dict[str, Any]:
        """Return current DHCP leases."""
        return await self._get("/monitor/system/dhcp/lease")

    # ── ARP / Neighbour ──────────────────────────────────

    async def list_arp_table(self) -> list[dict[str, Any]]:
        return await self._get("/cmdb/system/arp", scope="vdom")

    # ── Sessions ──────────────────────────────────────────

    async def list_sessions(self, filter_str: str = "") -> dict[str, Any]:
        """
        Return active firewall sessions.
        filter_str — e.g. 'srcaddr=10.0.0.1' to filter results.
        """
        path = "/monitor/firewall/session"
        if filter_str:
            path = f"{path}?filter={filter_str}"
        return await self._get(path)

    # ── HA / Cluster ──────────────────────────────────────

    async def get_ha_status(self) -> dict[str, Any]:
        """Return HA cluster status and member info."""
        return await self._get("/monitor/cluster/ha")

    # ── BGP ───────────────────────────────────────────────

    async def get_bgp_config(self) -> dict[str, Any]:
        """Return BGP router configuration (AS number, router-id, neighbors, networks)."""
        return await self._get("/cmdb/router/bgp", scope="vdom")

    async def list_bgp_neighbors(self) -> list[dict[str, Any]]:
        """Return configured BGP neighbors."""
        return await self._get("/cmdb/router/bgp/neighbor", scope="vdom")

    async def list_bgp_networks(self) -> list[dict[str, Any]]:
        """Return BGP advertised networks."""
        return await self._get("/cmdb/router/bgp/network", scope="vdom")

    async def get_bgp_neighbor_status(self) -> dict[str, Any]:
        """Return live BGP neighbor status — state, prefix counts, uptime."""
        return await self._get("/monitor/router/bgp/neighbors")

    async def get_bgp_rib(self) -> dict[str, Any]:
        """Return BGP Routing Information Base (RIB) — learned routes."""
        return await self._get("/monitor/router/bgp/rib")

    # ── System Info (read-only) ────────────────────────────

    async def get_system_status(self) -> dict[str, Any]:
        return await self._get("/monitor/system/status")

    async def get_firmware(self) -> dict[str, Any]:
        return await self._get("/monitor/system/firmware")

    async def get_license_info(self) -> dict[str, Any]:
        return await self._get("/monitor/license/status")

    # ── Internals ───────────────────────────────────────────

    async def _get(self, path: str, **kwargs: Any) -> Any:
        resp = await self._http.get(path, **kwargs)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = await self._http.post(path, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def _put(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = await self._http.put(path, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def _delete(self, path: str) -> dict[str, Any]:
        resp = await self._http.delete(path)
        resp.raise_for_status()
        return resp.json()
