# 🛡️ FortiGate MCP Server

> Give your AI agent full control over FortiGate firewalls — in plain English.

**FortiGate MCP Server** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
server that lets any MCP-compatible AI agent manage FortiGate firewalls through a
type-safe set of tools — no CLI expertise or API knowledge required.

**Works with:** [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Claude Code](https://docs.anthropic.com/en/docs/claude-code) · [any MCP client](https://modelcontextprotocol.io/implementations)

---

## ✨ Features

- **🌐 Multi-device** — Manage one or many FortiGates from a single server
- **🔒 Token-based auth** — REST API tokens, no username/password stored
- **📋 Full CRUD** — Addresses, policies, services, interfaces, routes
- **📊 Read-only views** — System status, license info, firmware version
- **⚡ Async** — Built on `httpx` async HTTP client
- **🐍 Python** — Pure Python, no native dependencies, pip-installable

---

## 🛠️ Available Tools (53 total)

Every tool accepts an optional `device` parameter to target a specific FortiGate.

### 📋 Core Firewall

| Tool | Description |
|------|-------------|
| `fortigate_list_addresses` | List all firewall address objects |
| `fortigate_create_address` | Create an address (ipmask / iprange / fqdn / dynamic) |
| `fortigate_delete_address` | Delete an address by name |
| `fortigate_list_policies` | List all firewall policies |
| `fortigate_create_policy` | Create a permit or deny policy |
| `fortigate_delete_policy` | Delete a policy by ID |
| `fortigate_list_services` | List all custom service objects |
| `fortigate_create_service` | Create a TCP/UDP/SCTP/ICMP service |
| `fortigate_delete_service` | Delete a service by name |

### 🔌 VPN

| Tool | Description |
|------|-------------|
| `fortigate_list_sslvpn_settings` | SSLVPN portal settings (IP pool, DNS, tunnel mode) |
| `fortigate_list_sslvpn_users` | Local SSLVPN users |
| `fortigate_list_sslvpn_groups` | SSLVPN user groups |
| `fortigate_list_sslvpn_connections` | Active SSLVPN connections (who is connected now) |
| `fortigate_list_ipsec_phase1` | IPSec phase-1 (IKE) tunnel configs |
| `fortigate_list_ipsec_phase2` | IPSec phase-2 (ESP) tunnel configs |
| `fortigate_list_ipsec_connections` | Active IPSec tunnel status |

### 👤 User & Authentication

| Tool | Description |
|------|-------------|
| `fortigate_list_users` | Local user accounts |
| `fortigate_list_user_groups` | Local user groups |
| `fortigate_list_authenticated_users` | Currently authenticated users |

### 📶 WiFi Controller

| Tool | Description |
|------|-------------|
| `fortigate_list_wifi_ap` | Managed Access Points (AP) — name, model, IP, status |
| `fortigate_list_wifi_ssid` | SSID (WLAN) configurations |
| `fortigate_list_wifi_clients` | Connected WiFi clients |

### 🔒 Security Profiles

| Tool | Description |
|------|-------------|
| `fortigate_list_antivirus_profiles` | Antivirus profiles |
| `fortigate_list_ips_profiles` | IPS sensor profiles |
| `fortigate_list_webfilter_profiles` | Web filter profiles |
| `fortigate_list_application_lists` | Application control lists |

### 🌐 Network

| Tool | Description |
|------|-------------|
| `fortigate_list_interfaces` | All network interfaces |
| `fortigate_list_routes` | Static routes |
| `fortigate_list_dhcp_server` | DHCP server configurations |
| `fortigate_list_dhcp_leases` | Current DHCP leases |
| `fortigate_list_arp_table` | ARP table (IP → MAC) |
| `fortigate_list_sessions` | Active firewall sessions (filterable) |

### 🔀 BGP

| Tool | Description |
|------|-------------|
| `fortigate_get_bgp_config` | BGP router config — AS number, router-id, neighbors |
| `fortigate_list_bgp_neighbors` | Configured BGP neighbors — remote AS, IP, description |
| `fortigate_list_bgp_networks` | BGP advertised networks |
| `fortigate_get_bgp_neighbor_status` | Live neighbor status — Established/Idle, prefix counts, uptime |
| `fortigate_get_bgp_rib` | BGP RIB — all learned routes with next-hop and AS-path |

### 🔁 OSPF

| Tool | Description |
|------|-------------|
| `fortigate_get_ospf_config` | OSPF router config — area, networks, passive interfaces |
| `fortigate_list_ospf_neighbor` | OSPF neighbor table — router-id, state, interface, dead timer |
| `fortigate_get_ospf_interface` | OSPF interface configs — area, cost, hello/dead intervals |
| `fortigate_get_ospf_network` | OSPF network definitions — area, prefix |
| `fortigate_get_ospf_status` | Live OSPF LSDB and routing info |

### 📡 RIP

| Tool | Description |
|------|-------------|
| `fortigate_get_rip_config` | RIP router config — version, timers, passive interfaces |
| `fortigate_list_rip_neighbor` | RIP neighbor table |
| `fortigate_get_rip_status` | Live RIP routing table — learned routes and metrics |

### 🎛️ Route Policy

| Tool | Description |
|------|-------------|
| `fortigate_list_route_maps` | Route maps — used for routing policy control |
| `fortigate_list_prefix_lists` | IPv4 prefix lists — BGP/OSPF route filtering |
| `fortigate_list_prefix_list6` | IPv6 prefix lists |
| `fortigate_list_access_lists` | Access (route) lists — legacy route filtering |

### 🖥️ System

| Tool | Description |
|------|-------------|
| `fortigate_list_devices` | Discover all registered FortiGate devices |
| `fortigate_get_status` | System status (serial, firmware, HA, uptime) |
| `fortigate_get_license` | License info (FortiCare, AV, IPS, VM) |
| `fortigate_get_ha_status` | HA cluster status (primary, sync, members) |

---

## 🔧 Quick Start

### 1 — Python Environment Setup (Ubuntu)

```bash
# Install Python 3.10+ if not already present
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Clone the repo (or if already cloned, just cd into it)
git clone https://github.com/winzeny/fortigate-mcp-server.git
cd fortigate-mcp-server

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .
```

> 💡 To deactivate the virtual environment, run: `deactivate`
> To reactivate it later: `source .venv/bin/activate`

### 2 — Install

```bash
pip install -e .
```

or from GitHub:

```bash
pip install git+https://github.com/winzeny/fortigate-mcp-server.git
```

### 3 — Get a FortiGate API Token

1. FortiGate GUI → **System → Administrators** → Create New
2. Type: **REST API Admin**
3. Set **Trusted Hosts** to the IP of this server (e.g. your workstation)
4. Copy the generated token — it is shown **only once**

> ⚠️ Store the token securely. It grants the same privileges as the admin that created it.

### 4 — Configure

**Environment variables** (for the default / primary device):

```bash
cp .env.example .env
# edit .env with your FortiGate host and API token
```

```env
FORTIGATE_HOST=https://10.0.0.1
FORTIGATE_API_TOKEN=your-token-here
FORTIGATE_VDOM=root
FORTIGATE_INSECURE=false
```

**Additional devices** — edit `config/devices.yaml`:

```yaml
devices:
  - name: hq-fw
    host: https://10.0.0.1
    api_token: hq-token
    vdom: root
    verify_ssl: true

  - name: branch-fw
    host: https://10.0.1.1
    api_token: branch-token
    vdom: root
    verify_ssl: true

  - name: lab-fw
    host: https://192.168.1.1
    api_token: lab-token
    vdom: lab-vdom
    verify_ssl: false   # self-signed cert only
```

### 5 — Register with Hermes Agent

Add to **`~/.hermes/config.yaml`**:

```yaml
mcp_servers:
  fortigate:
    command: "python"
    args: ["-m", "fortigate_mcp.server"]
```

Restart the gateway:

```bash
hermes gateway restart
```

### 6 — Use in plain English

```
You: Show me all registered FortiGate devices
→ fortigate_list_devices()

You: List firewall policies on the branch firewall
→ fortigate_list_policies(device="branch-fw")

You: Create an address for the internal network 10.0.0.0/24 called internalLAN
→ fortigate_create_address(
     name="internalLAN",
     address_type="ipmask",
     address="10.0.0.0/24",
     device="hq-fw"
   )

You: Create a policy allowing port 443 from internalLAN to any
→ fortigate_create_policy(
     src_intf="port1",
     dst_intf="port2",
     src_addr="internalLAN",
     dst_addr="all",
     service="HTTPS",
     device="hq-fw"
   )
```

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AI Agent                            │
│   (Hermes Agent, Claude Code, any MCP client)          │
└─────────────────────┬───────────────────────────────────┘
                      │  stdio · JSON-RPC
                      ▼
          ┌───────────────────────────┐
          │   fortigate-mcp-server   │
          │  python -m fortigate_mcp  │
          └─────────────┬─────────────┘
                        │  HTTPS + Bearer Token
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  HQ FW   │ │ Branch FW│ │  Lab FW  │
    │10.0.0.1  │ │10.0.1.1  │ │192.168.1.1│
    └──────────┘ └──────────┘ └──────────┘
```

---

## 🛡️ FortiGate Setup

The server talks to FortiGate through its REST API. No agent or package needs to be installed on the firewall itself.

### 1 — Create a REST API Admin

```
FortiGate GUI → System → Administrators → Create New
```

| Field | Value |
|-------|-------|
| **Type** | `REST API Admin` |
| **Username** | `mcp-server` (or any name) |
| **Trusted Hosts** | `IP of the machine running this server` — e.g. `192.168.1.100/32` |
| **Admin Profile** | `super_admin` (or a custom profile, see below) |
| **VDOM** | `root` (or the VDOM you want to manage) |

> ⚠️ **Trusted Hosts is critical.** Without it, anyone with the token can access your FortiGate from any IP.

### 2 — Copy the API Token

After clicking **OK**, a popup will show the **API Token**. Copy and store it immediately — it is shown **only once**.

```
┌──────────────────────────────────────────────┐
│  Your API Token                             │
│  ════════════════════════════════════════   │
│  nxxxxxxx0qGzP8xxxxxxxxxxxxxxxxxxxxxxxxxx  │
│                                              │
│  ⚠️ Copy and store this token securely.    │
│     It will not be shown again.             │
└──────────────────────────────────────────────┘
```

### 3 — Minimum Admin Profile (Optional)

Instead of `super_admin`, create a custom profile with only the permissions the MCP server needs:

| Permission | Required For |
|------------|-------------|
| `firewall address` — Read/Write | Create/delete address objects |
| `firewall policy` — Read/Write | Create/delete policies |
| `firewall service` — Read/Write | Create/delete service objects |
| `system interface` — Read | List interfaces |
| `router static` — Read | List routes |
| `system performance` — Read | Get system status |
| `system license` — Read | Get license info |

### 4 — Verify Connectivity

From the machine running the MCP server, test that the token works:

```bash
curl -s -X GET "https://<FORTIGATE_IP>/api/v2/monitor/system/status" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json"
```

A valid JSON response means the firewall is ready. Paste the token into your `.env` or `config/devices.yaml` and the MCP server will connect automatically.

---

## 🔐 Security Best Practices

| Rule | Why |
|------|-----|
| Always set **Trusted Hosts** | Token only works from your management subnet |
| Follow **least privilege** | Give each token only the permissions it needs |
| Never commit `.env` or `devices.yaml` | Both contain secrets — keep them local |
| `verify_ssl: false` only for lab/dev | Self-signed certs are not safe in production |

---

## 📁 Project Structure

```
fortigate-mcp-server/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
│   └── devices.yaml          ← add your devices here
└── src/fortigate_mcp/
    ├── __init__.py
    ├── client.py             ← async FortiGate REST API client + registry
    ├── tools.py              ← 14 MCP tool implementations
    └── server.py             ← MCP stdio server entry point
```

---

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Verify tool registration
python -c "
from fortigate_mcp.server import _make_tools
print(f'{len(_make_tools())} tools registered')
"

# Run tests
pytest

# Lint
ruff check src/
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Credits

Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
and [httpx](https://www.python-httpx.org/). Compatible with any MCP-compatible AI agent.
