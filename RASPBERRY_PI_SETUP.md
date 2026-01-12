# 🍓 AI-Firewall op Raspberry Pi 4 (8GB) - Complete Setup

## 🎯 Wat Wordt Geblokkeerd?

Je AI-Firewall detecteert en blokkeert **CICIDS2017 attack types**:

### ✅ Suricata IDS Detecteert (Signature-based):
1. **DDoS Attacks**
   - SYN Flood
   - UDP Flood
   - ICMP Flood
   - Slowloris
   
2. **Port Scanning**
   - Nmap scans
   - SYN scans
   - FIN scans
   - NULL scans
   
3. **Brute Force Attacks**
   - SSH brute force
   - FTP brute force
   - Web login attacks
   
4. **Web Attacks**
   - SQL Injection
   - Cross-Site Scripting (XSS)
   - Path Traversal
   - Command Injection
   
5. **Infiltration**
   - Remote exploits
   - Backdoor connections
   - Trojan activity
   
6. **Botnet Activity**
   - C2 communication
   - IRC botnets
   - Malware callbacks
   
7. **Exploits**
   - Buffer overflows
   - CVE exploits
   - Zero-day attempts

### ✅ ML Model Detecteert (Behavioral):
1. **Unknown DDoS variants** (niet in Suricata rules)
2. **Polymorphic attacks** (veranderende signatures)
3. **Low-and-slow attacks** (onder radar van Suricata)
4. **Zero-day exploits** (nog geen signature)
5. **Advanced evasion techniques**

### 🔥 Dual-Layer Protection:
```
Network Traffic
       ↓
   Suricata IDS (Layer 1)
       ├─→ Known threats → BLOCK
       ├─→ High-confidence → BLOCK  
       └─→ Suspicious → ML Validation (Layer 2)
                            ├─→ Malicious → BLOCK
                            └─→ Benign → ALLOW
```

**Voordeel:** 
- Suricata = Snel (0.1ms) voor bekende threats
- ML = Accuraat voor onbekende threats
- Minder false positives door dubbele check

---

## 🚀 Hardware Setup

### Minimale Vereisten:
- **Raspberry Pi 4 (8GB RAM)** ✅
- **2x Gigabit Ethernet**:
  - Built-in: eth0 (WAN)
  - USB 3.0 adapter: eth1 (LAN)
- **32GB+ SD Card** (Class 10 of beter)
- **Koeling:** Heatsink + Fan (CPU blijft <70°C)
- **Power:** 5V 3A adapter

### Netwerk Topologie:
```
Internet
   ↓
Modem
   ↓
┌──────────────────────┐
│  Raspberry Pi 4      │
│  ┌────────────────┐  │
│  │ eth0 (WAN)     │← Modem
│  │ eth1 (LAN)     │→ Router
│  │                │  │
│  │ Suricata IDS   │  │
│  │ ML Firewall    │  │
│  │ Auto-Block     │  │
│  └────────────────┘  │
└──────────────────────┘
   ↓
Router (192.168.1.1)
   ↓
LAN Devices
```

---

## 📦 Software Installatie

### 1. Raspberry Pi OS Installatie

```bash
# Download Raspberry Pi OS Lite (64-bit)
# https://www.raspberrypi.com/software/operating-systems/

# Flash naar SD card met Raspberry Pi Imager

# SSH enable tijdens flash (Settings → SSH)
```

### 2. Systeem Update

```bash
# SSH naar RPi
ssh pi@raspberrypi.local

# Update systeem
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y git curl wget htop iotop iftop
```

### 3. Docker Installatie (ARM64)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker pi

# Logout en login opnieuw
exit
ssh pi@raspberrypi.local

# Test
docker --version
# Output: Docker version 24.x.x

# Install Docker Compose
sudo apt install -y docker-compose
```

### 4. Network Bridge Setup

```bash
# Enable IP forwarding
sudo nano /etc/sysctl.conf

# Add:
net.ipv4.ip_forward=1
net.ipv4.conf.all.forwarding=1

# Apply
sudo sysctl -p

# Setup bridge (transparent inline mode)
sudo nano /etc/network/interfaces.d/bridge

# Add:
auto br0
iface br0 inet static
    address 192.168.100.1
    netmask 255.255.255.0
    bridge_ports eth0 eth1
    bridge_stp off
    bridge_fd 0

# Reboot
sudo reboot
```

### 5. Clone AI-Firewall Repository

```bash
# Clone repo
cd ~
git clone https://github.com/jouw-repo/ai-firewall.git
cd ai-firewall

# Of kopieer vanaf je Windows machine:
scp -r "C:\My Web Sites\ML" pi@raspberrypi.local:~/ai-firewall
```

---

## 🐳 Docker Deployment (Geoptimaliseerd voor RPi)

### 1. Build en Start

```bash
cd ~/ai-firewall

# Build images (eerste keer duurt ~10 min)
docker-compose -f docker-compose-rpi.yml build

# Start stack
docker-compose -f docker-compose-rpi.yml up -d

# Check status
docker-compose -f docker-compose-rpi.yml ps
```

### 2. Verwachte Output

```
NAME                    STATUS              PORTS
ai-firewall-suricata   Up (healthy)        -
ai-firewall-engine     Up (healthy)        -
ai-firewall-api        Up (healthy)        0.0.0.0:8000->8000/tcp
ai-firewall-dashboard  Up (healthy)        0.0.0.0:80->80/tcp
ai-firewall-redis      Up (healthy)        0.0.0.0:6379->6379/tcp
```

### 3. Check Logs

```bash
# Suricata logs
docker-compose -f docker-compose-rpi.yml logs -f suricata

# ML blocker logs
docker-compose -f docker-compose-rpi.yml logs -f ai-firewall-engine

# Alle logs
docker-compose -f docker-compose-rpi.yml logs -f
```

---

## 🎛️ Configuratie

### 1. Suricata Rules Update

```bash
# Update Suricata rules (in container)
docker exec -it ai-firewall-suricata suricata-update

# Or manually:
docker exec -it ai-firewall-suricata suricata-update \
  --suricata /usr/bin/suricata \
  --suricata-conf /etc/suricata/suricata.yaml

# Reload Suricata
docker restart ai-firewall-suricata
```

### 2. ML Threshold Aanpassen

```bash
# Edit config
nano ~/ai-firewall/config.json

# Change:
{
  "firewall": {
    "auto_block": true,
    "block_threshold": 0.7,  # Lower = more sensitive (0.5-0.9)
    "ml_validation": true    # Use ML for Suricata alerts
  }
}

# Restart
docker-compose -f docker-compose-rpi.yml restart ai-firewall-engine
```

### 3. Whitelist IPs

```bash
# Edit config
nano ~/ai-firewall/config.json

# Add:
{
  "firewall": {
    "whitelist": [
      "192.168.1.1",      # Router
      "192.168.1.100",    # Your PC
      "8.8.8.8",          # Google DNS
      "1.1.1.1"           # Cloudflare DNS
    ]
  }
}
```

---

## 📊 Monitoring

### 1. Web Dashboard

```
Open browser op LAN device:
http://192.168.100.1/

Tabs:
- Overview: Live stats
- Blocked IPs: Manage blocked IPs
- Logs: Suricata + ML alerts
- Settings: Configuration
```

### 2. CLI Monitoring

```bash
# System resources
htop

# Network traffic
sudo iftop -i eth0

# Disk I/O
sudo iotop

# Docker stats
docker stats

# Blocked IPs
docker exec ai-firewall-engine python -c \
  "from firewall_blocker import FirewallBlocker; \
   b = FirewallBlocker(); \
   print(b.get_blocked_ips())"
```

### 3. Suricata Stats

```bash
# Suricata statistics
docker exec ai-firewall-suricata suricatasc -c "dump-counters"

# Live alerts
tail -f ~/ai-firewall/logs/suricata/fast.log

# EVE JSON (for ML)
tail -f ~/ai-firewall/logs/suricata/eve.json | jq
```

---

## ⚡ Performance

### Verwachte Metrics (RPi 4 8GB):

```
CPU Usage:
- Idle: 5-10%
- Normal traffic: 20-30%
- Heavy attack: 50-70%

RAM Usage:
- Suricata: ~1.5 GB
- ML Engine: ~500 MB
- API + Dashboard: ~300 MB
- Redis: ~50 MB
Total: ~2.5 GB (5 GB free)

Latency:
- Suricata inspection: ~0.5ms
- ML validation: ~50ms (alleen voor suspicious flows)
- Total added latency: ~2-5ms (gaming safe!)

Throughput:
- Max: 940 Mbps (Gigabit)
- Typical: 500-800 Mbps (met inspectie)
```

### Optimalisaties:

```bash
# Disable ML voor snelheid (alleen Suricata)
nano config.json
# Set: "ml_validation": false

# Reduce Suricata rules
docker exec -it ai-firewall-suricata nano /etc/suricata/suricata.yaml
# Set: rule-files: [suricata.rules, local.rules]  # Alleen essentials

# Lower Suricata logging
# Set: default-log-level: warning
```

---

## 🔧 Troubleshooting

### 1. Suricata Niet Gestart

```bash
# Check logs
docker logs ai-firewall-suricata

# Common: Interface niet gevonden
# Fix: Change eth0 naar juiste interface
ip a  # Check interface naam

# Edit docker-compose-rpi.yml
nano docker-compose-rpi.yml
# Change: -i eth0 → -i wlan0 (of andere interface)
```

### 2. ML Model Laadt Niet

```bash
# Check model files
ls -lh ~/ai-firewall/models/

# Re-download models (vanaf Windows machine)
scp -r "C:\My Web Sites\ML\models" pi@raspberrypi.local:~/ai-firewall/

# Rebuild
docker-compose -f docker-compose-rpi.yml build ai-firewall-engine
docker-compose -f docker-compose-rpi.yml up -d
```

### 3. High CPU Usage

```bash
# Check wat CPU gebruikt
docker stats

# Als Suricata te veel CPU:
# Disable flow tracking
docker exec -it ai-firewall-suricata nano /etc/suricata/suricata.yaml
# Set: flow.managers: 1  (was 2)

# Restart
docker restart ai-firewall-suricata
```

### 4. SD Card Vol

```bash
# Check ruimte
df -h

# Cleanup logs
sudo docker system prune -a
rm -rf ~/ai-firewall/logs/*.log

# Rotate logs (cron)
sudo nano /etc/cron.daily/ai-firewall-cleanup
# Add:
#!/bin/bash
find /home/pi/ai-firewall/logs -name "*.log" -mtime +7 -delete
docker system prune -f

sudo chmod +x /etc/cron.daily/ai-firewall-cleanup
```

---

## 🧪 Testing

### 1. Test Suricata Detection

```bash
# Generate test alert (safe)
curl http://testmynids.org/uid/index.html

# Check Suricata fast.log
tail -f ~/ai-firewall/logs/suricata/fast.log

# Should see: GPL ATTACK_RESPONSE id check returned root
```

### 2. Test Auto-Blocking

```bash
# Simulate port scan (from another machine)
nmap -sS 192.168.100.1

# Check blocked IPs
docker exec ai-firewall-engine python -c \
  "from firewall_blocker import FirewallBlocker; \
   b = FirewallBlocker(); \
   print('\n'.join(b.get_blocked_ips()))"

# Should see your scanning IP blocked
```

### 3. Test ML Validation

```bash
# Check ML logs
docker logs ai-firewall-engine | grep "ML Prediction"

# Should see:
# [ML] Validating with machine learning...
# ML Prediction: MALICIOUS
# ML Score: 0.856
# [CONFIRMED] ML confirms threat!
```

---

## 🔐 Security Hardening

```bash
# 1. Change default password
passwd

# 2. Disable SSH password login (use keys)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no

# 3. Setup firewall (allow only SSH + Dashboard)
sudo apt install ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # Dashboard
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 4. Auto-updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📈 Production Checklist

- [ ] RPi 4 8GB met cooling
- [ ] 2x Gigabit Ethernet adapters
- [ ] 32GB+ SD card (Class 10)
- [ ] Raspberry Pi OS 64-bit geïnstalleerd
- [ ] Docker + Docker Compose installed
- [ ] Network bridge configured (br0)
- [ ] AI-Firewall stack running
- [ ] Suricata rules updated
- [ ] ML models loaded
- [ ] Whitelist configured
- [ ] Dashboard toegankelijk
- [ ] Logs rotation configured
- [ ] Auto-blocking getest
- [ ] Backup van config.json

---

## 🎉 Klaar!

**Je Raspberry Pi 4 draait nu als enterprise-grade firewall!**

**Capabilities:**
✅ Suricata IDS/IPS (signature-based)
✅ ML Behavioral Analysis (anomaly detection)
✅ Automatic IP blocking (iptables)
✅ Real-time monitoring dashboard
✅ <5ms latency (gaming safe)
✅ 500+ Mbps throughput
✅ Low power (~15W total)

**Cost: ~€100 vs €1000+ commercial firewall** 🔥
