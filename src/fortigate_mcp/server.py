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
                    "device": {
                        "type": "string",
                        "default": "default",
                        "description": "FortiGate device name (from fortigate_list_devices)",
                    },
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
                    "address_type": {
                        "type": "string",
                        "enum": ["ipmask", "iprange", "fqdn", "dynamic"],
                    },
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
                "properties": {
                    "name": {"type": "string"},
                    "device": {"type": "string", "default": "default"},
                },
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
                "properties": {
                    "policy_id": {"type": "integer"},
                    "device": {"type": "string", "default": "default"},
                },
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
                "properties": {
                    "name": {"type": "string"},
                    "device": {"type": "string", "default": "default"},
                },
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
            description="Get license information for a FortiGate.",
            inputSchema={
                "type": "object",
                "properties": {"device": {"type": "string", "default": "default"}},
            },
        ),
    ]


# ─── Dispatch ────────────────────────────────────────────────────────────────

async def _call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    args = arguments or {}

    dispatch: dict[str, Any] = {
        # Meta
        "fortigate_list_devices": ft.fortigate_list_devices,
        # Addresses
        "fortigate_list_addresses": lambda: ft.fortigate_list_addresses(
            device=str(args.get("device", "default")),
        ),
        "fortigate_create_address": lambda: ft.fortigate_create_address(
            name=str(args["name"]),
            address_type=str(args["address_type"]),
            address=str(args["address"]),
            interface=str(args.get("interface", "")),
            comment=str(args.get("comment", "")),
            device=str(args.get("device", "default")),
        ),
        "fortigate_delete_address": lambda: ft.fortigate_delete_address(
            name=str(args["name"]),
            device=str(args.get("device", "default")),
        ),
        # Policies
        "fortigate_list_policies": lambda: ft.fortigate_list_policies(
            device=str(args.get("device", "default")),
        ),
        "fortigate_create_policy": lambda: ft.fortigate_create_policy(
            src_intf=str(args["src_intf"]),
            dst_intf=str(args["dst_intf"]),
            src_addr=str(args["src_addr"]),
            dst_addr=str(args["dst_addr"]),
            service=str(args["service"]),
            action=str(args.get("action", "accept")),
            schedule=str(args.get("schedule", "always")),
            comment=str(args.get("comment", "")),
            device=str(args.get("device", "default")),
        ),
        "fortigate_delete_policy": lambda: ft.fortigate_delete_policy(
            policy_id=int(args["policy_id"]),
            device=str(args.get("device", "default")),
        ),
        # Services
        "fortigate_list_services": lambda: ft.fortigate_list_services(
            device=str(args.get("device", "default")),
        ),
        "fortigate_create_service": lambda: ft.fortigate_create_service(
            name=str(args["name"]),
            protocol=str(args["protocol"]),
            ports=str(args.get("ports", "")),
            comment=str(args.get("comment", "")),
            device=str(args.get("device", "default")),
        ),
        "fortigate_delete_service": lambda: ft.fortigate_delete_service(
            name=str(args["name"]),
            device=str(args.get("device", "default")),
        ),
        # Interfaces / Routes
        "fortigate_list_interfaces": lambda: ft.fortigate_list_interfaces(
            device=str(args.get("device", "default")),
        ),
        "fortigate_list_routes": lambda: ft.fortigate_list_routes(
            device=str(args.get("device", "default")),
        ),
        # System
        "fortigate_get_status": lambda: ft.fortigate_get_status(
            device=str(args.get("device", "default")),
        ),
        "fortigate_get_license": lambda: ft.fortigate_get_license(
            device=str(args.get("device", "default")),
        ),
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
