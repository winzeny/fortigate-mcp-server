# FortiGate MCP Server

A **Model Context Protocol (MCP)** server that gives AI agents (including Hermes Agent) a type-safe way to manage **one or more FortiGate firewalls** via the REST API.

---

## What it does

Once registered, the AI can call named tools such as:

| Tool | What it does |
|------|--------------|
| `fortigate_list_devices` | Discover all registered FortiGate devices |
| `fortigate_list_addresses` | List firewall address objects |
| `fortigate_create_address` | Create an address object (ipmask / iprange / fqdn / dynamic) |
| `fortigate_delete_address` | Delete an address by name |
| `fortigate_list_policies` | List all firewall policies |
| `fortigate_create_policy` | Create a permit/deny policy |
| `fortigate_delete_policy` | Delete a policy by ID |
| `fortigate_list_services` | List custom service objects |
| `fortigate_create_service` | Create a TCP/UDP/SCTP/ICMP service |
| `fortigate_delete_service` | Delete a service by name |
| `fortigate_list_interfaces` | List all network interfaces |
| `fortigate_list_routes` | List static routes |
| `fortigate_get_status` | Get system status (serial, firmware, HA, uptime) |
| `fortigate_get_license` | Get license information |

Every tool accepts an optional `device` parameter to target a specific FortiGate — e.g. `fortigate_list_policies(device="hq-fw")`.

---

## Architecture

```
AI Agent (Hermes)
       │
       │  stdio (JSON-RPC)
       ▼
fortigate-mcp-server   ◄── python -m fortigate_mcp.server
       │
       │  HTTPS + Bearer token (per device)
       ▼
  ┌─────────────┐   ┌─────────────┐
  │  FortiGate   │   │  FortiGate  │
  │  HQ (10.0.0.1)  │   │  Branch (10.0.1.1) │
  └─────────────┘   └─────────────┘
```

---

## Quick Start

### 1 — Install

```bash
git clone https://github.com/your-org/fortigate-mcp-server.git
cd fortigate-mcp-server
pip install -e .
```

### 2 — Configure your FortiGate devices

**Default device** (always required, credentials from env vars):

```bash
cp .env.example .env
# edit .env with your primary FortiGate host and API token
```

**Additional devices** — add to `config/devices.yaml`:

```yaml
devices:
  - name: hq-fw
    host: https://10.0.0.1
    api_token: your-hq-token
    vdom: root
    verify_ssl: true

  - name: branch-fw
    host: https://10.0.1.1
    api_token: your-branch-token
    vdom: root
    verify_ssl: true
```

#### Getting a FortiGate API Token

1. FortiGate GUI → **System → Administrators** → Create New
2. Type: **REST API Admin**
3. Set **Trusted Hosts** to the IP of this server
4. Copy the generated token — it is shown only once

> ⚠️ Store tokens securely. Never commit `.env` to version control.

### 3 — Register with Hermes Agent

Add to **`~/.hermes/config.yaml`**:

```yaml
mcp_servers:
  fortigate:
    command: "python"
    args: ["-m", "fortigate_mcp.server"]
```

Then restart the gateway:

```bash
hermes gateway restart
```

### 4 — Use in plain English

```
AI: "Show me all registered FortiGate devices"
  → fortigate_list_devices()

AI: "List firewall policies on the branch firewall"
  → fortigate_list_policies(device="branch-fw")

AI: "Create an address object for the internal network 10.0.0.0/24 called internalLan on the HQ firewall"
  → fortigate_create_address(
      name="internalLan",
      address_type="ipmask",
      address="10.0.0.0/24",
      device="hq-fw"
    )
```

---

## Multi-Device Design

```
.env                          config/devices.yaml
────────────                  ─────────────────────
FORTIGATE_HOST ──────────►  [default device]
FORTIGATE_API_TOKEN ──────►
FORTIGATE_VDOM ──────────►
FORTIGATE_INSECURE ──────►  [additional devices...]
                              - hq-fw
                              - branch-fw
                              - lab-fw
```

The AI calls `fortigate_list_devices()` first to discover what's available. All subsequent tools accept an optional `device` parameter — omitting it targets the default device (env vars).

---

## Security Notes

* Each API token grants the same privileges as the admin that created it — follow the **principle of least privilege**
* Set a **Trusted Host** on each REST API admin so tokens only work from your management subnet
* Never commit `.env` or any file containing real credentials to version control
* Use `verify_ssl: false` only for devices with self-signed certificates (lab/dev only)

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Verify all imports and tool registration
python -c "from fortigate_mcp import tools; from fortigate_mcp.server import _make_tools; print(f'{len(_make_tools())} tools OK')"

# Run tests (when added)
pytest
```
