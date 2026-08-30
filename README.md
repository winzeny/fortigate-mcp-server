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

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| `fortigate_list_devices` | Discover all registered FortiGate devices |
| `fortigate_list_addresses` | List all firewall address objects |
| `fortigate_create_address` | Create an address (ipmask / iprange / fqdn / dynamic) |
| `fortigate_delete_address` | Delete an address by name |
| `fortigate_list_policies` | List all firewall policies |
| `fortigate_create_policy` | Create a permit or deny policy |
| `fortigate_delete_policy` | Delete a policy by ID |
| `fortigate_list_services` | List all custom service objects |
| `fortigate_create_service` | Create a TCP/UDP/SCTP/ICMP service |
| `fortigate_delete_service` | Delete a service by name |
| `fortigate_list_interfaces` | List all network interfaces |
| `fortigate_list_routes` | List all static routes |
| `fortigate_get_status` | Get system status (serial, firmware, HA, uptime) |
| `fortigate_get_license` | Get license information |

Every tool accepts an optional `device` parameter to target a specific firewall.

---

## 🔧 Quick Start

### 1 — Install

```bash
pip install -e .
```

or from GitHub:

```bash
pip install git+https://github.com/winzeny/fortigate-mcp-server.git
```

### 2 — Get a FortiGate API Token

1. FortiGate GUI → **System → Administrators** → Create New
2. Type: **REST API Admin**
3. Set **Trusted Hosts** to the IP of this server (e.g. your workstation)
4. Copy the generated token — it is shown **only once**

> ⚠️ Store the token securely. It grants the same privileges as the admin that created it.

### 3 — Configure

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

### 4 — Register with Hermes Agent

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

### 5 — Use in plain English

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

## 🔐 Security

| Rule | Why |
|------|-----|
| Use **Trusted Hosts** on REST API admins | Token only works from your management subnet |
| Principle of **least privilege** | Give each token only the permissions it needs |
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
