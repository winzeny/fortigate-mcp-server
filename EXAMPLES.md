# FortiGate MCP Server — Usage Examples

> ตัวอย่างการใช้งาน tools ทั้ง 70 ตัว แบ่งตามหมวดหมู่
>
> ทุก tool รองรับ parameter `device` — ใส่ชื่อ device ที่ register ไว้ใน `config/devices.yaml`
> ถ้าไม่ใส่ จะใช้ device ที่ตั้งเป็น `default`

---

## 📋 Core Firewall

### Address Objects

```python
# ดู address objects ทั้งหมด
fortigate_list_addresses(device="hq-fw")
# → [{"name": "internalLAN", "type": "ipmask", "subnet": "10.0.0.0/24"}, ...]

# สร้าง address ใหม่ — IP range
fortigate_create_address(
    name="dhcp-pool",
    address_type="iprange",
    address="10.0.10.1-10.0.10.254",
    device="hq-fw"
)

# สร้าง address แบบ FQDN
fortigate_create_address(
    name="google-dns",
    address_type="fqdn",
    address="google.com",
    device="hq-fw"
)

# ลบ address
fortigate_delete_address(name="old-server", device="hq-fw")
```

### Firewall Policies

```python
# ดู policies ทั้งหมด
fortigate_list_policies(device="hq-fw")
# → [{"id": 1, "srcintf": "port1", "dstintf": "port2", "action": "accept"}, ...]

# สร้าง policy — allow HTTPS จาก internal ไป internet
fortigate_create_policy(
    src_intf="port1",
    dst_intf="port2",
    src_addr="internalLAN",
    dst_addr="all",
    service="HTTPS",
    device="hq-fw"
)

# สร้าง policy — deny กำหนด comment ด้วย
fortigate_create_policy(
    src_intf="port1",
    dst_intf="port2",
    src_addr="10.0.0.0/24",
    dst_addr="all",
    service="HTTP,HTTPS",
    action="deny",
    comment="block web for guest vlan",
    device="hq-fw"
)

# ลบ policy
fortigate_delete_policy(policy_id=25, device="hq-fw")
```

### Service Objects

```python
# ดู custom services
fortigate_list_services(device="hq-fw")

# สร้าง service ใหม่ — TCP range
fortigate_create_service(
    name="app-db",
    protocol="TCP",
    ports="5432-5433",
    comment="PostgreSQL database",
    device="hq-fw"
)

# สร้าง service — UDP single port
fortigate_create_service(
    name="voip-sip",
    protocol="UDP",
    ports="5060",
    device="hq-fw"
)

# ลบ service
fortigate_delete_service(name="app-db", device="hq-fw")
```

---

## 🔌 VPN

### SSLVPN

```python
# ดู SSLVPN settings — IP pool, DNS, tunnel mode
fortigate_list_sslvpn_settings(device="hq-fw")
# → {"ip_pool": ["10.10.0.0/24"], "dns_server": "8.8.8.8", "tunnel_mode": true}

# ดู SSLVPN users
fortigate_list_sslvpn_users(device="hq-fw")
# → [{"name": "win", "status": "up", "ip": "10.10.0.5", "login_time": "..."}]

# ดู SSLVPN groups
fortigate_list_sslvpn_groups(device="hq-fw")

# ดูว่าใครกำลัง connect อยู่
fortigate_list_sslvpn_connections(device="hq-fw")
# → [{"user": "win", "group": "vpn-users", "ip": "10.10.0.5", "duration": "2h 34m"}]
```

### IPSec VPN

```python
# ดู IPSec phase-1 (IKE) configs
fortigate_list_ipsec_phase1(device="hq-fw")
# → [{"name": "to-branch", "remote_gateway": "103.20.1.1", "interface": "port1"}]

# ดู IPSec phase-2 (ESP) configs
fortigate_list_ipsec_phase2(device="hq-fw")
# → [{"name": "to-branch-p2", "phase1": "to-branch", "crypto": "aes256-sha256"}]

# ดู active IPSec tunnels ว่าตัวไหน up อยู่
fortigate_list_ipsec_connections(device="hq-fw")
# → [{"tunnel": "to-branch", "status": "up", "bytes_in": 1234567, "bytes_out": 987654}]
```

---

## 👤 User & Authentication

```python
# ดู local users ทั้งหมด
fortigate_list_users(device="hq-fw")
# → [{"name": "admin", "type": "local", "status": "enable"}, ...]

# ดู user groups
fortigate_list_user_groups(device="hq-fw")
# → [{"name": "vpn-users", "members": ["win", "job"]}, ...]

# ดูว่าใคร login อยู่บน firewall ตอนนี้
fortigate_list_authenticated_users(device="hq-fw")
# → [{"user": "admin", "auth_method": "local", "login_time": "2026-08-30T09:00", "ip": "10.0.0.50"}]
```

---

## 📶 WiFi Controller

```python
# ดู managed APs — ตัวไหน online/offline
fortigate_list_wifi_ap(device="hq-fw")
# → [{"name": "AP-1F", "model": "FAP-223E", "ip": "10.0.1.10", "status": "up", "clients": 42}]

# ดู SSID configurations
fortigate_list_wifi_ssid(device="hq-fw")
# → [{"ssid": "Company-WiFi", "security": "WPA2-Enterprise", "vlan": 10}, ...]

# ดู client ที่ต่อ WiFi อยู่
fortigate_list_wifi_clients(device="hq-fw")
# → [{"mac": "AA:BB:CC:DD:EE:FF", "ssid": "Company-WiFi", "ap": "AP-1F", "ip": "10.0.10.25"}]
```

---

## 🔒 Security Profiles

```python
# ดู antivirus profiles
fortigate_list_antivirus_profiles(device="hq-fw")

# ดู IPS sensor profiles
fortigate_list_ips_profiles(device="hq-fw")

# ดู web filter profiles
fortigate_list_webfilter_profiles(device="hq-fw")

# ดู application control lists
fortigate_list_application_lists(device="hq-fw")
```

---

## 🌐 Network

```python
# ดู interfaces ทั้งหมด
fortigate_list_interfaces(device="hq-fw")
# → [{"name": "port1", "ip": "10.0.0.1/24", "status": "up", "type": "physical"}, ...]

# ดู static routes
fortigate_list_routes(device="hq-fw")
# → [{"dst": "0.0.0.0/0", "gateway": "10.0.0.1", "device": "port1"}, ...]

# ดู DHCP server configs
fortigate_list_dhcp_server(device="hq-fw")
# → [{"interface": "port2", "range": "10.0.20.1-10.0.20.254", "gateway": "10.0.20.1"}]

# ดู DHCP leases — IP ที่ถูกจ่ายไปแล้ว
fortigate_list_dhcp_leases(device="hq-fw")
# → [{"ip": "10.0.20.50", "mac": "AA:BB:CC:DD:EE:FF", "hostname": "laptop-win", "expires": "2026-08-31T09:00"}]

# ดู ARP table
fortigate_list_arp_table(device="hq-fw")
# → [{"ip": "10.0.0.10", "mac": "AA:BB:CC:DD:EE:FF", "interface": "port1"}]

# ดู active sessions (filter ได้)
fortigate_list_sessions(device="hq-fw")
# หรือ filter ด้วย source IP
fortigate_list_sessions(filter="srcaddr=10.0.0.50", device="hq-fw")
```

---

## 🛤️ Routing

### Static / Policy Route

```python
# ดู static routes
fortigate_list_static_routes(device="hq-fw")
# → [{"seq": 1, "dst": "0.0.0.0/0", "gateway": "10.0.0.1", "device": "port1", "distance": 10}]

# ดู IPv6 static routes
fortigate_list_static_routes6(device="hq-fw")

# ดู policy routes
fortigate_list_policy_routes(device="hq-fw")
# → [{"seq": 1, "input": "port1", "src": "10.0.0.0/24", "dst": "203.0.113.0/24", "gateway": "10.0.0.254"}]

# ดู IPv6 policy routes
fortigate_list_policy_routes6(device="hq-fw")
```

### BGP

```python
# ดู BGP config — AS number, router-id
fortigate_get_bgp_config(device="hq-fw")
# → {"as": 65001, "router_id": "10.0.0.1", "neighbors": [...]}

# ดู configured BGP neighbors
fortigate_list_bgp_neighbors(device="hq-fw")
# → [{"ip": "203.0.113.2", "remote_as": 65002, "description": "ISP-1"}]

# ดู advertised networks
fortigate_list_bgp_networks(device="hq-fw")
# → [{"prefix": "10.0.0.0/8"}, ...]

# ดู live neighbor status — Established หรือยัง, prefix count
fortigate_get_bgp_neighbor_status(device="hq-fw")
# → [{"neighbor": "203.0.113.2", "state": "Established", "prefixes_in": 1523, "uptime": "5d 03h"}]

# ดู BGP RIB — route ที่เรียนรู้มาจาก BGP
fortigate_get_bgp_rib(device="hq-fw")
# → [{"prefix": "203.0.113.0/24", "next_hop": "203.0.113.2", "as_path": "65002 65003"}]
```

### OSPF

```python
# ดู OSPF config
fortigate_get_ospf_config(device="hq-fw")
# → {"as": 65001, "area": "0.0.0.0", "passive": ["port2"]}

# ดู OSPF neighbors
fortigate_list_ospf_neighbor(device="hq-fw")
# → [{"router_id": "10.0.0.2", "state": "Full", "interface": "port2", "dead": "00:00:35"}]

# ดู OSPF interface configs
fortigate_get_ospf_interface(device="hq-fw")
# → [{"interface": "port2", "area": "0.0.0.0", "cost": 10, "hello": 10, "dead": 40}]

# ดู OSPF network definitions
fortigate_get_ospf_network(device="hq-fw")

# ดู live OSPF LSDB และ routing info
fortigate_get_ospf_status(device="hq-fw")
```

### RIP

```python
# ดู RIP config
fortigate_get_rip_config(device="hq-fw")

# ดู RIP neighbors
fortigate_list_rip_neighbor(device="hq-fw")

# ดู live RIP routing table
fortigate_get_rip_status(device="hq-fw")
```

### Route Policy

```python
# ดู route maps
fortigate_list_route_maps(device="hq-fw")
# → [{"name": "RM-BGP-IN", "seq": 10, "match": "aspath", "set": "localpref 200"}]

# ดู IPv4 prefix lists
fortigate_list_prefix_lists(device="hq-fw")
# → [{"name": "PL-BLOCK", "rules": [{"seq": 1, "prefix": "10.0.0.0/8", "action": "deny"}]}]

# ดู IPv6 prefix lists
fortigate_list_prefix_list6(device="hq-fw")

# ดู access lists (legacy)
fortigate_list_access_lists(device="hq-fw")
```

---

## 🌐 SD-WAN

```python
# ดู SD-WAN config — zones, members, health-check
fortigate_get_sdwan_config(device="hq-fw")

# ดู SD-WAN member interfaces
fortigate_list_sdwan_members(device="hq-fw")
# → [{"seq": 1, "interface": "port1", "gateway": "10.0.0.1", "status": "alive"},
#     {"seq": 2, "interface": "port2", "gateway": "10.1.0.1", "status": "dead"}]

# ดู SD-WAN service rules
fortigate_list_sdwan_rules(device="hq-fw")
# → [{"name": "WEB-TRAFFIC", "strategy": "sla", "sla": "primary-link", "members": [1]}]

# ดู SD-WAN SLA thresholds
fortigate_list_sdwan_sla(device="hq-fw")
# → [{"name": "primary-link", "latency": 50, "jitter": 20, "packetloss": 1}]

# ดู live SD-WAN status — link quality ต่อ member
fortigate_get_sdwan_status(device="hq-fw")
# → [{"member": 1, "latency": 12, "jitter": 3, "packetloss": 0.1, "sla_pass": true},
#     {"member": 2, "latency": 0, "jitter": 0, "packetloss": 0, "sla_pass": false}]
```

---

## 📋 Logs

```python
# ดูว่ามี log categories อะไรบ้าง
fortigate_list_log_categories(device="hq-fw")
# → ["traffic", "event", "dns", "attack", "app-ctrl"]

# ดู local log settings
fortigate_get_log_settings(device="hq-fw")
# → {"level": "information", "format": "text", "device": "memory", "max_size_mb": 50}

# ดู log forwarding destinations (syslog / FortiAnalyzer)
fortigate_list_log_forward(device="hq-fw")

# ดู event logs — admin login, config changes
fortigate_get_log_events(device="hq-fw")
# → [{"time": "2026-08-30T09:00", "type": "event", "subtype": "system", "message": "Admin login successful"}]

# ดู event logs filter by user
fortigate_get_log_events(filter="user=admin", device="hq-fw")

# ดู traffic logs — ใครไปไหน
fortigate_get_traffic_logs(device="hq-fw")
# → [{"time": "...", "src": "10.0.0.50", "dst": "8.8.8.8", "action": "accept", "bytes": 12345}]

# ดู traffic logs filter เฉพาะ deny
fortigate_get_traffic_logs(filter="action=deny", device="hq-fw")

# ดู traffic logs filter เฉพาะ destination IP
fortigate_get_traffic_logs(filter="dst=1.1.1.1", device="hq-fw")

# ดู attack/intrusion logs
fortigate_get_attack_logs(device="hq-fw")
# → [{"time": "...", "signature": "ET SCAN Potential SSH Scan", "severity": "medium", "src": "203.0.113.10"}]

# ดู attack logs filter by severity
fortigate_get_attack_logs(filter="severity=critical", device="hq-fw")

# ดู DNS query logs
fortigate_get_dns_logs(device="hq-fw")
# → [{"time": "...", "domain": "google.com", "ip": "142.250.80.46", "qtype": "A"}]

# ดู DNS logs filter by domain
fortigate_get_dns_logs(filter="domain=facebook.com", device="hq-fw")

# ดู application control logs
fortigate_get_app_control_logs(device="hq-fw")
# → [{"time": "...", "app_id": 2, "app_name": "Facebook", "action": "block", "bytes": 0}]
```

---

## 🖥️ System

```python
# ค้นหา devices ที่ register ไว้
fortigate_list_devices()
# → [{"name": "default", "host": "https://10.0.0.1", "vdom": "root"}, ...]

# ดู system status
fortigate_get_status(device="hq-fw")
# → {"serial": "FG100E-xxx", "version": "v7.4.11", "ha_mode": "Standalone", "uptime": "45d 12h"}

# ดู license info
fortigate_get_license(device="hq-fw")
# → {"forticare": "registered", "av": "valid", "ips": "valid", "vm": "valid"}

# ดู HA cluster status
fortigate_get_ha_status(device="hq-fw")
# → [{"name": "FG100E-1", "role": "primary", "sync_status": "in-sync"},
#     {"name": "FG100E-2", "role": "secondary", "sync_status": "in-sync"}]
```

---

## 🔍 Real-World Scenarios

### "มีใคร login เข้า firewall วันนี้บ้าง?"
```
fortigate_get_log_events(filter="subtype=admin", device="hq-fw")
```

### "ดู traffic ที่โดน block ในชั่วโมงที่ผ่านมา"
```
fortigate_get_traffic_logs(filter="action=deny", device="hq-fw")
```

### "เช็ค SD-WAN links ว่าตัวไหน down"
```
fortigate_get_sdwan_status(device="hq-fw")
# → member 2 มี sla_pass: false = link มีปัญหา
```

### "ดู BGP neighbor ที่ยังไม่ Established"
```
fortigate_get_bgp_neighbor_status(device="hq-fw")
# → state: "Idle" หมายถึงยังไม่เชื่อมต่อ
```

### "มีใครใช้ SSLVPN อยู่บ้าง?"
```
fortigate_list_sslvpn_connections(device="hq-fw")
```

### "ดู DHCP leases ว่า IP อะไรถูกจ่ายไป"
```
fortigate_list_dhcp_leases(device="hq-fw")
```

### "เช็คว่า AP ตัวไหน offline"
```
fortigate_list_wifi_ap(device="hq-fw")
# → status: "down" = AP ปิดหรือเสีย
```

### "ดู policy ที่ allow อะไรขึ้น internet"
```
fortigate_list_policies(device="hq-fw")
# → ดู action=accept แถวแรกๆ
```

### "ดู routes ที่มี 0.0.0.0/0 (default route)"
```
fortigate_list_routes(device="hq-fw")
# → dst: "0.0.0.0/0" = default gateway
```

### "มี attack จาก IP ไหนบ้าง"
```
fortigate_get_attack_logs(filter="severity=high", device="hq-fw")
```

---

## 🔀 BGP — Real-World Scenarios

### "BGP neighbor ยังไม่ Established — ดูสถานะ"
```
fortigate_get_bgp_neighbor_status(device="hq-fw")
```
**ผลลัพธ์:**
```json
[
  {"neighbor": "203.0.113.2", "remote_as": 65002, "state": "Idle",       "prefixes_in": 0},
  {"neighbor": "203.0.113.6", "remote_as": 65003, "state": "Established","prefixes_in": 4821}
]
```
**วิเคราะห์:** neighbor `203.0.113.2` ยัง Idle อยู่ — เช็คว่า BGP session สร้างได้ไหม, ACL บล็อก port 179 หรือเปล่า, หรือ remote AS ถูกต้องไหม

---

### "ดูว่า BGP รับ route มาจาก ISP กี่ prefix"
```
fortigate_get_bgp_neighbor_status(device="hq-fw")
```
**ผลลัพธ์:**
```json
{"neighbor": "203.0.113.2", "state": "Established", "prefixes_in": 12453, "prefixes_out": 3}
```
**วิเคราะห์:** รับ 12,453 prefix มาจาก ISP — ปกติ full table จะประมาณ 900K+ prefix ถ้าน้อยกว่านี้มาก อาจมี route filter ติดมา

---

### "ดู BGP routes ที่เรียนรู้มาทั้งหมด (RIB)"
```
fortigate_get_bgp_rib(device="hq-fw")
```
**ผลลัพธ์ (ตัวอย่าง):**
```json
[
  {"prefix": "1.0.0.0/24",    "next_hop": "203.0.113.2", "as_path": "15169"},
  {"prefix": "8.8.0.0/16",    "next_hop": "203.0.113.2", "as_path": "15169 3356"},
  {"prefix": "10.0.0.0/8",    "next_hop": "0.0.0.0",    "as_path": "65001",  "origin": "IGP"},
  {"prefix": "192.168.0.0/16", "next_hop": "0.0.0.0",    "as_path": "65001",  "origin": "IGP"}
]
```
**วิเคราะห์:**
- `as_path: 15169` = route มาจาก Google (AS15169) ผ่าน ISP
- `as_path: 3356` = มาจาก Level3
- `next_hop: 0.0.0.0` + `origin: IGP` = route ที่เราประกาศเอง (network statement หรือ redistribute)

---

### "เช็ค AS-Path ของ route ไปยัง Facebook (_AS 32934_)"
```
fortigate_get_bgp_rib(device="hq-fw")
# Facebook อยู่ AS32934
```
**ผลลัพธ์:**
```json
{"prefix": "157.240.0.0/16", "next_hop": "203.0.113.2", "as_path": "65001 174 32934"}
```
**วิเคราะห์:** AS-Path = `เรา(65001) → Cogent(174) → Facebook(32934)` — path ถูกต้อง ถ้าต้องการ path สำรอง ดูว่า AS นี้มาจาก ISP อื่นได้ไหม

---

### "ดูว่ามี route ที่มาจาก AS ต่างๆ กี่ AS"
```
fortigate_get_bgp_rib(device="hq-fw")
```
**วิเคราะห์:** ดู AS-path ที่ซ้ำๆ — ถ้าเห็น `as_path: "65001 174"` เยอะๆ แปลว่า traffic วิ่งผ่าน Cogent เป็นหลัก — ถ้ามี ISP สำรอง อาจอยากให้วิ่งผ่าน AS อื่นบ้าง

---

### "ดู advertised networks — เราประกาศอะไรออกไป"
```
fortigate_list_bgp_networks(device="hq-fw")
```
**ผลลัพธ์:**
```json
[
  {"prefix": "10.0.0.0/8",     "origin": "IGP"},
  {"prefix": "103.20.190.0/24","origin": "IGP"}
]
```
**วิเคราะห์:** ประกาศ private `10.0.0.0/8` ออกไปด้วย — ต้องตรวจสอบ route map filter ว่าปิด private IP ออกไปแล้ว

---

### "ดู configured neighbors — remote-as อะไรไว้"
```
fortigate_list_bgp_neighbors(device="hq-fw")
```
**ผลลัพธ์:**
```json
[
  {"neighbor": "203.0.113.2", "remote_as": 65002, "description": "ISP-Primary"},
  {"neighbor": "203.0.113.6", "remote_as": 65003, "description": "ISP-Backup"}
]
```
**วิเคราะห์:** มี 2 ISP — ต้องตรวจสอบว่าใช้ AS-path prepend หรือ MED ตั้งค่า preference ระหว่าง 2 ISP ยังไง

---

### "ดู BGP config — AS, router-id, timers"
```
fortigate_get_bgp_config(device="hq-fw")
```
**ผลลัพธ์:**
```json
{
  "as": 65001,
  "router_id": "10.0.0.1",
  "keepalive": 30,
  "holdtime": 90,
  "ebgp_multihop": 1
}
```
**วิเคราะห์:**
- `ebgp_multihop: 1` = eBGP ตรง physical interface ถ้าใช้ loopback ต้อง set = 2+
- `router_id` ต้อง match กับ OSPF router-id ถ้าใช้ redistribute ระหว่างกัน

---

### "BGP neighbor มี flapping — เช็ค uptime"
```
fortigate_get_bgp_neighbor_status(device="hq-fw")
```
**ผลลัพธ์:**
```json
{"neighbor": "203.0.113.2", "state": "Established", "uptime": "00:02:34", "prefixes_in": 4821}
```
**วิเคราะห์:** uptime แค่ 2 นาที = session พึ่ง establish ใหม่ = flapping! ดูว่า interface มี error หรือ ISP มีปัญหา

---

### "เช็ค prefix ที่รับมาจาก ISP — มี private IP รั่วไหม (route leak)"
```
fortigate_get_bgp_rib(device="hq-fw")
```
**ผลลัพธ์:**
```json
{"prefix": "10.0.0.0/8",    "next_hop": "203.0.113.2", "as_path": "65001 174"},
{"prefix": "172.16.0.0/12",  "next_hop": "203.0.113.2", "as_path": "65001 174"}
```
**วิเคราะห์:** มี RFC1918 private ranges (10.0.0.0/8, 172.16.0.0/12) รับเข้ามา! — ต้องมี prefix-list filter บน inbound ปิด private IP

---

### "เช็ค multi-path — route ไป AS เดียวกันมาจากหลาย ISP"
```
fortigate_get_bgp_rib(device="hq-fw")
```
**ผลลัพธ์:**
```json
{"prefix": "8.8.8.0/24", "next_hop": "203.0.113.2", "as_path": "65001 174 15169"},
{"prefix": "8.8.8.0/24", "next_hop": "203.0.113.6", "as_path": "65001 65003 15169"}
```
**วิเคราะห์:** มี 2 path ไป `8.8.8.0/24` — วิ่งผ่าน ISP Primary และ Backup — ถ้าใช้ load-balance ต้องตรวจสอบ BGP best-path selection

---

### "ดูว่า route ไป prefix สำคัญ วิ่งผ่าน AS ไหน"
```
fortigate_get_bgp_rib(device="hq-fw")
# ดู prefix ที่มี as_path สั้นที่สุด = best path ของ BGP
```
**วิเคราะห์:** AS-path สั้นที่สุด = BGP ชอบที่สุด — ถ้าเห็นว่า route สำคัญ (เช่น Google, Cloudflare) วิ่งผ่าน ISP ที่ช้า อาจต้อง tune local-pref หรือ MED

---

## 🔁 OSPF — Real-World Scenarios

### "OSPF neighbor ตัวไหนยังไม่ Full"
```
fortigate_list_ospf_neighbor(device="hq-fw")
```
**ผลลัพธ์:**
```json
[
  {"router_id": "10.0.0.2", "state": "Full",  "interface": "port2", "dead": "00:00:32"},
  {"router_id": "10.0.0.3", "state": "2-Way", "interface": "port3", "dead": "00:00:45"}
]
```
**วิเคราะห์:** `2-Way` = neighbor รับ hello ได้แต่ยังไม่ถึง Full — อาจเป็น DR/BDR election issue หรือ MTU mismatch

---

### "ดู OSPF interface cost — คำนวณ route preference"
```
fortigate_get_ospf_interface(device="hq-fw")
```
**ผลลัพธ์:**
```json
[{"interface": "port2", "area": "0.0.0.0", "cost": 10, "hello": 10, "dead": 40}]
```

### "ดู OSPF LSDB มีปัญหาหรือเปล่า"
```
fortigate_get_ospf_status(device="hq-fw")
```

---

## 📡 RIP — Real-World Scenarios

### "เช็ค RIP neighbor ว่ายัง alive ไหม"
```
fortigate_list_rip_neighbor(device="hq-fw")
```

### "ดู routing table ที่เรียนรู้ผ่าน RIP"
```
fortigate_get_rip_status(device="hq-fw")
```
