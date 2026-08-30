"""
FortiGate MCP Server entry point — multi-device.

Implements the Model Context Protocol server interface (stdio transport).
Run with: python -m fortigate_mcp.server

In ~/.hermes/config.yaml:

  mcp_servers:
    fortigate:
      command: "python"
      args: ["-m", "fortigate_mcp.server"]

Environment variables (for the 'default' device):

  FORTIGATE_HOST=https://10.0.0.1
  FORTIGATE_API_TOKEN=your-token
  FORTIGATE_VDOM=root
  FORTIGATE_INSECURE=false

Additional devices are loaded from config/devices.yaml — see that file
for the full schema.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult, ListToolsResult

from . import __version__
from . import tools as ft

APP_NAME = "FortiGate MCP Server"
server = Server(APP_NAME)


# ─── Tool schema ───────────────────────────────────────────────────────────────

def _make_tools() -> list[Tool]:
    return [
        # ── Meta ──
        Tool(
            name="fortigate_list_devices",
            description="List all registered FortiGate devices. "
            "Use this first to discover which devices are available. "
            "Returns name, host, VDOM, SSL verify setting, and which is the default.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Addresses ──
        Tool(
            name="fortigate_list_addresses",
            description="List all firewall address objects on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {"type": "string", "default": "default", "description": "FortiGate device name"},
                },
            },
        ),
        Tool(
            name="fortigate_create_address",
            description="Create a firewall address object on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique address object name"},
                    "address_type": {"type": "string", "enum": ["ipmask", "iprange", "fqdn", "dynamic"]},
                    "address": {"type": "string", "description": "IP/CIDR, range, or FQDN"},
                    "interface": {"type": "string", "description": "Bound interface (optional)"},
                    "comment": {"type": "string", "description": "Description (optional)"},
                    "device": {"type": "string", "default": "default"},
                },
                "required": ["name", "address_type", "address"],
            },
        ),
        Tool(
            name="fortigate_delete_address",
            description="Delete a firewall address object by name.",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}, "device": {"type": "string", "default": "default"}},
                "required": ["name"],
            },
        ),
        # ── Policies ──
        Tool(
            name="fortigate_list_policies",
            description="List all firewall policies on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_create_policy",
            description="Create a firewall policy on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "src_intf": {"type": "string"},
                    "dst_intf": {"type": "string"},
                    "src_addr": {"type": "string"},
                    "dst_addr": {"type": "string"},
                    "service": {"type": "string"},
                    "action": {"type": "string", "enum": ["accept", "deny"], "default": "accept"},
                    "schedule": {"type": "string", "default": "always"},
                    "comment": {"type": "string"},
                    "device": {"type": "string", "default": "default"},
                },
                "required": ["src_intf", "dst_intf", "src_addr", "dst_addr", "service"],
            },
        ),
        Tool(
            name="fortigate_delete_policy",
            description="Delete a firewall policy by its numeric ID.",
            inputSchema={
                "type": "object",
                "properties": {"policy_id": {"type": "integer"}, "device": {"type": "string", "default": "default"}},
                "required": ["policy_id"],
            },
        ),
        # ── Services ──
        Tool(
            name="fortigate_list_services",
            description="List all custom firewall service objects on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_create_service",
            description="Create a custom firewall service object on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "protocol": {"type": "string", "enum": ["TCP", "UDP", "SCTP", "ICMP", "IP"]},
                    "ports": {"type": "string", "description": "Port or range, e.g. '443' or '8000-8080'"},
                    "comment": {"type": "string"},
                    "device": {"type": "string", "default": "default"},
                },
                "required": ["name", "protocol"],
            },
        ),
        Tool(
            name="fortigate_delete_service",
            description="Delete a custom firewall service by name.",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}, "device": {"type": "string", "default": "default"}},
                "required": ["name"],
            },
        ),
        # ── Interfaces / Routes ──
        Tool(
            name="fortigate_list_interfaces",
            description="List all network interfaces on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_routes",
            description="List all static routes on a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── SSLVPN ──
        Tool(
            name="fortigate_list_sslvpn_settings",
            description="Get SSLVPN portal settings — IP pool, DNS, tunnel mode, portal type.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sslvpn_users",
            description="List local SSL VPN users on the FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sslvpn_groups",
            description="List SSL VPN user groups on the FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sslvpn_connections",
            description="List active SSLVPN connections — shows who is connected right now.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── IPSec VPN ──
        Tool(
            name="fortigate_list_ipsec_phase1",
            description="List IPSec phase-1 (IKE) tunnel configurations — name, remote gateway, interface.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_ipsec_phase2",
            description="List IPSec phase-2 (ESP) tunnel configurations — phase1 association, crypto settings.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_ipsec_connections",
            description="List active IPSec VPN tunnel status — shows which tunnels are up and byte counts.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── User / Authentication ──
        Tool(
            name="fortigate_list_users",
            description="List local user accounts on the FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_user_groups",
            description="List local user groups on the FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_authenticated_users",
            description="List currently authenticated firewall users — who is actively logged in.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── WiFi Controller ──
        Tool(
            name="fortigate_list_wifi_ap",
            description="List managed Access Points (AP) — name, model, IP, status, client count.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_wifi_ssid",
            description="List SSID (WLAN) configurations — SSID name, security, VLAN, AP.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_wifi_clients",
            description="List connected WiFi clients — shows who is on the wireless network.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── Security Profiles ──
        Tool(
            name="fortigate_list_antivirus_profiles",
            description="List antivirus profiles configured on the FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_ips_profiles",
            description="List IPS (Intrusion Prevention System) sensor profiles.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_webfilter_profiles",
            description="List web filter profiles configured on the FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_application_lists",
            description="List application control lists (application signatures).",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── DHCP ──
        Tool(
            name="fortigate_list_dhcp_server",
            description="List DHCP server configurations — scope, range, gateway, lease time.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_dhcp_leases",
            description="List current DHCP leases — shows assigned IPs, MACs, hostnames, expiry.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── ARP / Sessions ──
        Tool(
            name="fortigate_list_arp_table",
            description="List the ARP table — IP to MAC address mappings.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sessions",
            description="List active firewall sessions — optionally filter by source IP, destination, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter string, e.g. 'srcaddr=10.0.0.1'"},
                    "device": {"type": "string", "default": "default"},
                },
            },
        ),
        # ── HA ──
        Tool(
            name="fortigate_get_ha_status",
            description="Get HA cluster status — which unit is primary, sync state, member list.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── BGP ──
        Tool(
            name="fortigate_get_bgp_config",
            description="Get BGP router configuration — AS number, router-id, neighbors, networks.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_bgp_neighbors",
            description="List configured BGP neighbors — remote AS, IP, description.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_bgp_networks",
            description="List BGP advertised networks — prefix and associated route map.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_bgp_neighbor_status",
            description="Get live BGP neighbor status — Established/Idle, prefix counts, uptime, last update.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_bgp_rib",
            description="Get BGP Routing Information Base (RIB) — all learned BGP routes with next-hop and AS-path.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── OSPF ──
        Tool(
            name="fortigate_get_ospf_config",
            description="Get OSPF router configuration — area, networks, passive interfaces.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_ospf_neighbor",
            description="List OSPF neighbor table — router-id, state (Full/2-Way), interface, dead timer.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_ospf_interface",
            description="Get OSPF interface configurations — area, cost, hello/dead intervals.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_ospf_network",
            description="Get OSPF network definitions — area, prefix.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_ospf_status",
            description="Get live OSPF LSDB and routing information.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── RIP ──
        Tool(
            name="fortigate_get_rip_config",
            description="Get RIP router configuration — version, timers, passive interfaces.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_rip_neighbor",
            description="List RIP neighbor table.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_rip_status",
            description="Get live RIP routing table — learned routes and metrics.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── Route Map / Prefix List / Access List ──
        Tool(
            name="fortigate_list_route_maps",
            description="List configured route maps — used for routing policy control.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_prefix_lists",
            description="List configured IPv4 prefix lists — used for BGP/OSPF route filtering.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_prefix_list6",
            description="List configured IPv6 prefix lists.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_access_lists",
            description="List configured access (route) lists — legacy route filtering.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── Static Route ──
        Tool(
            name="fortigate_list_static_routes",
            description="List IPv4 static routes — destination, gateway, device, distance, priority.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_static_routes6",
            description="List IPv6 static routes.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── Policy Route ──
        Tool(
            name="fortigate_list_policy_routes",
            description="List IPv4 policy routes — input device, source/dest, gateway, output interface.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_policy_routes6",
            description="List IPv6 policy routes.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── SD-WAN ──
        Tool(
            name="fortigate_get_sdwan_config",
            description="Get SD-WAN zone configuration — zones, members assigned, health-check settings.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sdwan_members",
            description="List SD-WAN member interfaces — interface name, gateway, IP, status (alive/dead).",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sdwan_rules",
            description="List SD-WAN service rules — name, strategy (spoke/sla), SLA target, load-balance method.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_sdwan_sla",
            description="List SD-WAN SLA configurations — latency, jitter, packet-loss thresholds.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_sdwan_status",
            description="Get live SD-WAN status — per-member link quality (latency/jitter/packet-loss), SLA status.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        # ── Logs ──
        Tool(
            name="fortigate_list_log_categories",
            description="List available log categories — traffic, dns, event, attack, app-ctrl, etc.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_log_settings",
            description="Get local log settings — log level, format, device, memory buffer size.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_list_log_forward",
            description="List log forwarding profiles — syslog/FortiAnalyzer destinations.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_log_events",
            description="Get event logs — admin logins, config changes, system events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "FortiGate filter string, e.g. 'user=admin' (optional)"},
                    "device": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="fortigate_get_traffic_logs",
            description="Get recent traffic logs — source, dest, action, bytes, session ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "FortiGate filter string, e.g. 'dst=8.8.8.8' (optional)"},
                    "device": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="fortigate_get_attack_logs",
            description="Get intrusion/attack logs — signature, severity, source, destination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "FortiGate filter string (optional)"},
                    "device": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="fortigate_get_dns_logs",
            description="Get DNS query logs — domain, IP, query type, action.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "FortiGate filter string (optional)"},
                    "device": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="fortigate_get_app_control_logs",
            description="Get application control logs — app ID, category, action, bandwidth.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "FortiGate filter string (optional)"},
                    "device": {"type": "string", "default": "default"},
                },
            },
        ),
        # ── System (read-only) ──
        Tool(
            name="fortigate_get_status",
            description="Get FortiGate system status — serial, firmware version, HA mode, up-time.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
        Tool(
            name="fortigate_get_license",
            description="Get license information — FortiCare, IPS, AV, VM, etc.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
    ]


# ─── Dispatch ────────────────────────────────────────────────────────────────

async def _call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    args = arguments or {}
    dev = str(args.get("device", "default"))

    dispatch: dict[str, Any] = {
        # Meta
        "fortigate_list_devices": ft.fortigate_list_devices,
        # Addresses
        "fortigate_list_addresses": lambda: ft.fortigate_list_addresses(device=dev),
        "fortigate_create_address": lambda: ft.fortigate_create_address(
            name=str(args["name"]),
            address_type=str(args["address_type"]),
            address=str(args["address"]),
            interface=str(args.get("interface", "")),
            comment=str(args.get("comment", "")),
            device=dev,
        ),
        "fortigate_delete_address": lambda: ft.fortigate_delete_address(name=str(args["name"]), device=dev),
        # Policies
        "fortigate_list_policies": lambda: ft.fortigate_list_policies(device=dev),
        "fortigate_create_policy": lambda: ft.fortigate_create_policy(
            src_intf=str(args["src_intf"]),
            dst_intf=str(args["dst_intf"]),
            src_addr=str(args["src_addr"]),
            dst_addr=str(args["dst_addr"]),
            service=str(args["service"]),
            action=str(args.get("action", "accept")),
            schedule=str(args.get("schedule", "always")),
            comment=str(args.get("comment", "")),
            device=dev,
        ),
        "fortigate_delete_policy": lambda: ft.fortigate_delete_policy(policy_id=int(args["policy_id"]), device=dev),
        # Services
        "fortigate_list_services": lambda: ft.fortigate_list_services(device=dev),
        "fortigate_create_service": lambda: ft.fortigate_create_service(
            name=str(args["name"]),
            protocol=str(args["protocol"]),
            ports=str(args.get("ports", "")),
            comment=str(args.get("comment", "")),
            device=dev,
        ),
        "fortigate_delete_service": lambda: ft.fortigate_delete_service(name=str(args["name"]), device=dev),
        # Interfaces / Routes
        "fortigate_list_interfaces": lambda: ft.fortigate_list_interfaces(device=dev),
        "fortigate_list_routes": lambda: ft.fortigate_list_routes(device=dev),
        # SSLVPN
        "fortigate_list_sslvpn_settings": lambda: ft.fortigate_list_sslvpn_settings(device=dev),
        "fortigate_list_sslvpn_users": lambda: ft.fortigate_list_sslvpn_users(device=dev),
        "fortigate_list_sslvpn_groups": lambda: ft.fortigate_list_sslvpn_groups(device=dev),
        "fortigate_list_sslvpn_connections": lambda: ft.fortigate_list_sslvpn_connections(device=dev),
        # IPSec
        "fortigate_list_ipsec_phase1": lambda: ft.fortigate_list_ipsec_phase1(device=dev),
        "fortigate_list_ipsec_phase2": lambda: ft.fortigate_list_ipsec_phase2(device=dev),
        "fortigate_list_ipsec_connections": lambda: ft.fortigate_list_ipsec_connections(device=dev),
        # User / Auth
        "fortigate_list_users": lambda: ft.fortigate_list_users(device=dev),
        "fortigate_list_user_groups": lambda: ft.fortigate_list_user_groups(device=dev),
        "fortigate_list_authenticated_users": lambda: ft.fortigate_list_authenticated_users(device=dev),
        # WiFi
        "fortigate_list_wifi_ap": lambda: ft.fortigate_list_wifi_ap(device=dev),
        "fortigate_list_wifi_ssid": lambda: ft.fortigate_list_wifi_ssid(device=dev),
        "fortigate_list_wifi_clients": lambda: ft.fortigate_list_wifi_clients(device=dev),
        # Security Profiles
        "fortigate_list_antivirus_profiles": lambda: ft.fortigate_list_antivirus_profiles(device=dev),
        "fortigate_list_ips_profiles": lambda: ft.fortigate_list_ips_profiles(device=dev),
        "fortigate_list_webfilter_profiles": lambda: ft.fortigate_list_webfilter_profiles(device=dev),
        "fortigate_list_application_lists": lambda: ft.fortigate_list_application_lists(device=dev),
        # DHCP
        "fortigate_list_dhcp_server": lambda: ft.fortigate_list_dhcp_server(device=dev),
        "fortigate_list_dhcp_leases": lambda: ft.fortigate_list_dhcp_leases(device=dev),
        # ARP / Sessions
        "fortigate_list_arp_table": lambda: ft.fortigate_list_arp_table(device=dev),
        "fortigate_list_sessions": lambda: ft.fortigate_list_sessions(
            filter=str(args.get("filter", "")),
            device=dev,
        ),
        # HA
        "fortigate_get_ha_status": lambda: ft.fortigate_get_ha_status(device=dev),
        # BGP
        "fortigate_get_bgp_config": lambda: ft.fortigate_get_bgp_config(device=dev),
        "fortigate_list_bgp_neighbors": lambda: ft.fortigate_list_bgp_neighbors(device=dev),
        "fortigate_list_bgp_networks": lambda: ft.fortigate_list_bgp_networks(device=dev),
        "fortigate_get_bgp_neighbor_status": lambda: ft.fortigate_get_bgp_neighbor_status(device=dev),
        "fortigate_get_bgp_rib": lambda: ft.fortigate_get_bgp_rib(device=dev),
        # OSPF
        "fortigate_get_ospf_config": lambda: ft.fortigate_get_ospf_config(device=dev),
        "fortigate_list_ospf_neighbor": lambda: ft.fortigate_list_ospf_neighbor(device=dev),
        "fortigate_get_ospf_interface": lambda: ft.fortigate_get_ospf_interface(device=dev),
        "fortigate_get_ospf_network": lambda: ft.fortigate_get_ospf_network(device=dev),
        "fortigate_get_ospf_status": lambda: ft.fortigate_get_ospf_status(device=dev),
        # RIP
        "fortigate_get_rip_config": lambda: ft.fortigate_get_rip_config(device=dev),
        "fortigate_list_rip_neighbor": lambda: ft.fortigate_list_rip_neighbor(device=dev),
        "fortigate_get_rip_status": lambda: ft.fortigate_get_rip_status(device=dev),
        # Route Map / Prefix List / Access List
        "fortigate_list_route_maps": lambda: ft.fortigate_list_route_maps(device=dev),
        "fortigate_list_prefix_lists": lambda: ft.fortigate_list_prefix_lists(device=dev),
        "fortigate_list_prefix_list6": lambda: ft.fortigate_list_prefix_list6(device=dev),
        "fortigate_list_access_lists": lambda: ft.fortigate_list_access_lists(device=dev),
        # Static Route
        "fortigate_list_static_routes": lambda: ft.fortigate_list_static_routes(device=dev),
        "fortigate_list_static_routes6": lambda: ft.fortigate_list_static_routes6(device=dev),
        # Policy Route
        "fortigate_list_policy_routes": lambda: ft.fortigate_list_policy_routes(device=dev),
        "fortigate_list_policy_routes6": lambda: ft.fortigate_list_policy_routes6(device=dev),
        # SD-WAN
        "fortigate_get_sdwan_config": lambda: ft.fortigate_get_sdwan_config(device=dev),
        "fortigate_list_sdwan_members": lambda: ft.fortigate_list_sdwan_members(device=dev),
        "fortigate_list_sdwan_rules": lambda: ft.fortigate_list_sdwan_rules(device=dev),
        "fortigate_list_sdwan_sla": lambda: ft.fortigate_list_sdwan_sla(device=dev),
        "fortigate_get_sdwan_status": lambda: ft.fortigate_get_sdwan_status(device=dev),
        # Logs
        "fortigate_list_log_categories": lambda: ft.fortigate_list_log_categories(device=dev),
        "fortigate_get_log_settings": lambda: ft.fortigate_get_log_settings(device=dev),
        "fortigate_list_log_forward": lambda: ft.fortigate_list_log_forward(device=dev),
        "fortigate_get_log_events": lambda: ft.fortigate_get_log_events(
            filter=str(args.get("filter", "")),
            device=dev,
        ),
        "fortigate_get_traffic_logs": lambda: ft.fortigate_get_traffic_logs(
            filter=str(args.get("filter", "")),
            device=dev,
        ),
        "fortigate_get_attack_logs": lambda: ft.fortigate_get_attack_logs(
            filter=str(args.get("filter", "")),
            device=dev,
        ),
        "fortigate_get_dns_logs": lambda: ft.fortigate_get_dns_logs(
            filter=str(args.get("filter", "")),
            device=dev,
        ),
        "fortigate_get_app_control_logs": lambda: ft.fortigate_get_app_control_logs(
            filter=str(args.get("filter", "")),
            device=dev,
        ),
        # System
        "fortigate_get_status": lambda: ft.fortigate_get_status(device=dev),
        "fortigate_get_license": lambda: ft.fortigate_get_license(device=dev),
    }

    handler = dispatch.get(name)
    if handler is None:
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))],
            isError=True,
        )

    try:
        result: str = await handler()
        return CallToolResult(content=[TextContent(type="text", text=result)])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}))],
            isError=True,
        )


# ─── MCP handlers ───────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(tools=_make_tools())


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    return await _call_tool(name, arguments)


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    print(f"# {APP_NAME} v{__version__} starting …", file=sys.stderr)
    asyncio.run(main())
