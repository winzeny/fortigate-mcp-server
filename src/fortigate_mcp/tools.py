"""
MCP tool definitions for FortiGate — multi-device aware.

Every tool accepts an optional `device` parameter so the AI can target
a specific FortiGate by name, or default to the device marked "default".
"""

from __future__ import annotations

import json
from typing import Any

from .client import FortiGateClient, FortiGateDevice, MultiFortiGateRegistry

# ─── Singleton registry (lazy) ──────────────────────────────────────────────────

_registry: MultiFortiGateRegistry | None = None


def _reg() -> MultiFortiGateRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = MultiFortiGateRegistry()
    return _registry


# ─── Tool helpers ─────────────────────────────────────────────────────────────

def _ok(data: Any) -> str:
    return json.dumps({"success": True, "data": data}, indent=2)


def _err(msg: str) -> str:
    return json.dumps({"success": False, "error": msg}, indent=2)


# ─── Meta tools ──────────────────────────────────────────────────────────────

async def fortigate_list_devices() -> str:
    """
    List all registered FortiGate devices and their connection info.
    Use this first to discover which devices are available.
    """
    try:
        reg = _reg()
        devices = []
        for name in reg.device_names():
            dev = reg.get_device(name)
            devices.append({
                "name": dev.name,
                "host": dev.host,
                "vdom": dev.vdom,
                "verify_ssl": dev.verify_ssl,
                "is_default": name == reg.DEFAULT_NAME,
            })
        return _ok({"devices": devices})
    except Exception as e:
        return _err(str(e))


# ─── Firewall Address Tools ───────────────────────────────────────────────────

async def fortigate_list_addresses(device: str = "default") -> str:
    """
    List all firewall address objects on a FortiGate.
    device – name of the FortiGate device (from fortigate_list_devices)
    """
    try:
        data = await _reg().get_client(device).list_addresses()
        return _ok(data)
    except Exception as e:
        return _err(str(e))


async def fortigate_create_address(
    name: str,
    address_type: str,
    address: str,
    interface: str = "",
    comment: str = "",
    device: str = "default",
) -> str:
    """
    Create a firewall address object on a FortiGate.
    name         – unique address object name
    address_type – 'ipmask', 'iprange', 'fqdn', or 'dynamic'
    address      – IP/CIDR, range, or FQDN value
    interface    – bound interface (optional)
    comment      – description (optional)
    device       – target FortiGate device name (default: 'default')
    """
    try:
        payload: dict[str, Any] = {
            "name": name,
            "type": address_type,
            "subnet": address,
            "interface": interface,
            "comment": comment,
        }
        result = await _reg().get_client(device).create_address(payload)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


async def fortigate_delete_address(name: str, device: str = "default") -> str:
    """Delete a firewall address object by name on a FortiGate."""
    try:
        result = await _reg().get_client(device).delete_address(name)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


# ─── Firewall Policy Tools ────────────────────────────────────────────────────

async def fortigate_list_policies(device: str = "default") -> str:
    """
    List all firewall policies on a FortiGate.
    device – name of the FortiGate device
    """
    try:
        data = await _reg().get_client(device).list_policies()
        return _ok(data)
    except Exception as e:
        return _err(str(e))


async def fortigate_create_policy(
    src_intf: str,
    dst_intf: str,
    src_addr: str,
    dst_addr: str,
    service: str,
    action: str = "accept",
    schedule: str = "always",
    comment: str = "",
    device: str = "default",
) -> str:
    """
    Create a firewall policy on a FortiGate.
    src_intf   – source interface (e.g. port1)
    dst_intf   – destination interface (e.g. port2)
    src_addr   – source address object name or 'all'
    dst_addr   – destination address object name or 'all'
    service    – service object name or 'ALL'
    action     – 'accept' or 'deny' (default: accept)
    schedule   – schedule name or 'always' (default)
    comment    – description (optional)
    device     – target FortiGate device name (default: 'default')
    """
    try:
        payload: dict[str, Any] = {
            "name": f"policy-{src_intf}-to-{dst_intf}",
            "srcintf": [{"name": src_intf}],
            "dstintf": [{"name": dst_intf}],
            "srcaddr": [{"name": src_addr}],
            "dstaddr": [{"name": dst_addr}],
            "service": [{"name": service}],
            "action": action,
            "schedule": schedule,
            "status": "enable",
            "comments": comment,
        }
        result = await _reg().get_client(device).create_policy(payload)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


async def fortigate_delete_policy(policy_id: int, device: str = "default") -> str:
    """Delete a firewall policy by ID on a FortiGate."""
    try:
        result = await _reg().get_client(device).delete_policy(policy_id)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


# ─── Firewall Service Tools ───────────────────────────────────────────────────

async def fortigate_list_services(device: str = "default") -> str:
    """List all custom firewall service objects on a FortiGate."""
    try:
        data = await _reg().get_client(device).list_services()
        return _ok(data)
    except Exception as e:
        return _err(str(e))


async def fortigate_create_service(
    name: str,
    protocol: str,
    ports: str = "",
    comment: str = "",
    device: str = "default",
) -> str:
    """
    Create a custom firewall service object on a FortiGate.
    name     – unique service name
    protocol – 'TCP', 'UDP', 'SCTP', 'ICMP', or 'IP'
    ports    – port or range "8000-8080" (required for TCP/UDP/SCTP)
    comment  – description (optional)
    device   – target FortiGate device name (default: 'default')
    """
    try:
        payload: dict[str, Any] = {
            "name": name,
            "protocol": protocol,
            "comment": comment,
        }
        if protocol in ("TCP", "UDP", "SCTP") and ports:
            payload["tcp-portrange"] = ports
        result = await _reg().get_client(device).create_service(payload)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


async def fortigate_delete_service(name: str, device: str = "default") -> str:
    """Delete a custom firewall service by name on a FortiGate."""
    try:
        result = await _reg().get_client(device).delete_service(name)
        return _ok(result)
    except Exception as e:
        return _err(str(e))


# ─── Interface / Route Tools ──────────────────────────────────────────────────

async def fortigate_list_interfaces(device: str = "default") -> str:
    """List all network interfaces on a FortiGate."""
    try:
        data = await _reg().get_client(device).list_interfaces()
        return _ok(data)
    except Exception as e:
        return _err(str(e))


async def fortigate_list_routes(device: str = "default") -> str:
    """List all static routes on a FortiGate."""
    try:
        data = await _reg().get_client(device).list_routes()
        return _ok(data)
    except Exception as e:
        return _err(str(e))


# ─── System Info Tools (read-only) ────────────────────────────────────────────

async def fortigate_get_status(device: str = "default") -> str:
    """
    Get FortiGate system status — serial, firmware version, HA mode, up-time.
    device – name of the FortiGate device (default: 'default')
    """
    try:
        data = await _reg().get_client(device).get_system_status()
        return _ok(data)
    except Exception as e:
        return _err(str(e))


async def fortigate_get_license(device: str = "default") -> str:
    """Get license information for a FortiGate."""
    try:
        data = await _reg().get_client(device).get_license_info()
        return _ok(data)
    except Exception as e:
        return _err(str(e))
