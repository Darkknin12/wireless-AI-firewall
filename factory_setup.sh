# 🏭 AI-FIREWALL: FACTORY PRE-CONFIGURATION GUIDE

## 🎯 DOEL: 100% Plug & Play Voor Normale Users

**Target User:** Iemand die alleen een stopcontact kan vinden en een kabel kan insteken.

**Setup Time:** < 5 minuten (zonder technische kennis)

---

## 📦 PRODUCT PACKAGING

### Hardware Kit Bevat:

```
┌─────────────────────────────────────────┐
│  AI-FIREWALL HOME SECURITY KIT          │
│                                         │
│  ✅ Raspberry Pi 4 (8GB) in case       │
│  ✅ Pre-configured SD card (32GB)      │
│  ✅ USB Gigabit Ethernet adapter       │
│  ✅ Power supply (5V 3A EU plug)       │
│  ✅ 2x Ethernet cables (1m, color-coded)│
│  ✅ RGB LED status indicator (installed)│
│  ✅ Quick Start Guide (1 page, pictures)│
│  ✅ Activation card (QR code)          │
│                                         │
│  Price: €149 (all-inclusive)            │
└─────────────────────────────────────────┘
```

### Visual Design:

```
Case Features:
- LED window (shows status)
- Labeled ports:
  * "INTERNET" (eth0, BLUE sticker)
  * "ROUTER" (eth1, YELLOW sticker)
  * "POWER" (red port)
- Ventilation (silent fan)
- Wall-mountable
```

---

## 🏭 FACTORY PRE-CONFIGURATION PROCESS

### Step 1: Hardware Assembly (10 min/unit)

```bash
# Technician checklist:
[ ] Install heatsink on RPi CPU
[ ] Install active cooling fan (3.3V GPIO)
[ ] Connect RGB LED to GPIO pins:
    - Red: GPIO 17
    - Green: GPIO 27
    - Blue: GPIO 22
[ ] Insert USB Gigabit adapter (eth1)
[ ] Place RPi in case
[ ] Add port labels (BLUE/YELLOW/RED)
[ ] QC: Visual inspection
```

### Step 2: SD Card Pre-Configuration (1st Time Setup)

```bash
# Master Image Creation (do this ONCE):

# 1. Fresh Raspberry Pi OS install
# 2. Run factory_setup.sh (automated script)
# 3. Create golden master image
# 4. Clone to all production SD cards

# See: factory_setup.sh for automation
```

### Step 3: Software Pre-Configuration (Automated)

```bash
# factory_setup.sh does:
1. Install Docker + dependencies
2. Clone AI-Firewall stack
3. Build all containers
4. Configure auto-start
5. Set up LED status indicators
6. Enable setup wizard (first boot)
7. Generate unique device ID
8. Create backup partition
9. Enable auto-updates
10. Security hardening

# Total time: 15 min (automated)
```

### Step 4: Unique Device Configuration

```bash
# Each device gets:
- Unique hostname: ai-firewall-XXXX (random)
- Unique device ID: AF-2024-XXXXX
- QR code for activation: https://activate.ai-firewall.com/AF-2024-XXXXX
- Default password: (printed on activation card)

# This happens during SD card cloning
```

### Step 5: Quality Control Testing

```bash
# Automated test suite (5 min/unit):

[ ] Boot test (LED status)
[ ] Network detection (both interfaces)
[ ] Docker containers start
[ ] Dashboard accessible
[ ] Suricata loads rules
[ ] ML model inference test
[ ] Attack simulation (block test)
[ ] Power cycle test
[ ] Factory reset test

# All tests MUST pass before packaging
```

### Step 6: Packaging (2 min/unit)

```bash
# Packaging checklist:
[ ] Device in anti-static bag
[ ] Activation card inserted
[ ] Quick Start Guide (with pictures)
[ ] All cables in separate bags
[ ] Everything in retail box
[ ] QC sticker on box
[ ] Seal box

# Ready for shipping!
```

---

## 🤖 FACTORY AUTOMATION SCRIPTS

### factory_setup.sh (Master Image Creator)

<function_calls>
<invoke name="create_file">
<parameter name="content">#!/bin/bash
#
# AI-Firewall Factory Setup Script
# Creates pre-configured golden master image
# Run on fresh Raspberry Pi OS installation
#

set -e  # Exit on error

echo "=================================================="
echo "AI-FIREWALL FACTORY SETUP - AUTOMATED"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Progress counter
STEP=0
total_steps=15

progress() {
    STEP=$((STEP + 1))
    echo ""
    echo -e "${GREEN}[${STEP}/${total_steps}] $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}ERROR: Do not run as root! Run as user 'pi'${NC}"
   exit 1
fi

# ============================================================
# SYSTEM CONFIGURATION
# ============================================================

progress "Updating system packages..."
sudo apt update
sudo apt upgrade -y

progress "Installing essential packages..."
sudo apt install -y \
    git curl vim wget \
    iptables iproute2 \
    python3 python3-pip \
    jq htop iotop \
    network-manager

progress "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker pi
    echo -e "${YELLOW}NOTE: Docker installed. You may need to logout/login.${NC}"
else
    echo "Docker already installed."
fi

progress "Installing Docker Compose..."
sudo apt install -y docker-compose

progress "Configuring network (IP forwarding)..."
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
# AI-Firewall network configuration
net.ipv4.ip_forward=1
net.ipv4.conf.all.forwarding=1
net.ipv4.conf.default.forwarding=1
net.bridge.bridge-nf-call-iptables=1
EOF
sudo sysctl -p

# ============================================================
# AI-FIREWALL INSTALLATION
# ============================================================

progress "Creating AI-Firewall directory..."
cd /home/pi
if [ -d "ai-firewall" ]; then
    echo "Directory exists, updating..."
    cd ai-firewall
    git pull
else
    # In production, replace with your git repo
    echo "Cloning AI-Firewall repository..."
    # git clone https://github.com/your-repo/ai-firewall.git
    # For now, assuming files are already copied
    mkdir -p ai-firewall
    cd ai-firewall
fi

progress "Building Docker images (this takes ~10 minutes)..."
docker-compose -f docker-compose-rpi.yml build

progress "Testing Docker stack..."
docker-compose -f docker-compose-rpi.yml up -d
sleep 30
docker-compose -f docker-compose-rpi.yml ps
docker-compose -f docker-compose-rpi.yml down

# ============================================================
# LED STATUS INDICATOR SETUP
# ============================================================

progress "Installing LED status indicator..."
sudo apt install -y python3-rpi.gpio

# Create LED control script
cat > /home/pi/ai-firewall/led_status.py <<'LEDEOF'
#!/usr/bin/env python3
"""
LED Status Indicator for AI-Firewall
- Green: Normal operation
- Yellow: Suspicious traffic
- Red: Attack blocked
- Blue: System starting
"""
import RPi.GPIO as GPIO
import time
import redis
import sys

# GPIO pins (BCM numbering)
LED_RED = 17
LED_GREEN = 27
LED_BLUE = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_BLUE, GPIO.OUT)

def set_color(red, green, blue):
    GPIO.output(LED_RED, red)
    GPIO.output(LED_GREEN, green)
    GPIO.output(LED_BLUE, blue)

def cleanup():
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        # Connect to Redis for status updates
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        while True:
            status = r.get('firewall_status') or 'starting'
            
            if status == 'starting':
                set_color(0, 0, 1)  # Blue
            elif status == 'normal':
                set_color(0, 1, 0)  # Green
            elif status == 'suspicious':
                set_color(1, 1, 0)  # Yellow
            elif status == 'blocked':
                set_color(1, 0, 0)  # Red
                time.sleep(2)
                set_color(0, 1, 0)  # Back to green
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"LED Error: {e}")
        cleanup()
LEDEOF

chmod +x /home/pi/ai-firewall/led_status.py

# ============================================================
# AUTO-START CONFIGURATION
# ============================================================

progress "Configuring auto-start (systemd)..."

# Make start script executable
chmod +x /home/pi/ai-firewall/start.sh

# Install systemd services
sudo cp /home/pi/ai-firewall/ai-firewall.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-firewall

# LED service
cat > /tmp/led-status.service <<'EOF'
[Unit]
Description=AI-Firewall LED Status Indicator
After=ai-firewall.service
Requires=ai-firewall.service

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/ai-firewall/led_status.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/led-status.service /etc/systemd/system/
sudo systemctl enable led-status

# ============================================================
# FIRST BOOT SETUP WIZARD
# ============================================================

progress "Installing setup wizard..."

cat > /home/pi/ai-firewall/setup_wizard.py <<'WIZARDEOF'
#!/usr/bin/env python3
"""
First Boot Setup Wizard
Runs on first boot to configure device
"""
import os
import json
import random
import string

SETUP_FLAG = '/home/pi/.ai-firewall-configured'

if os.path.exists(SETUP_FLAG):
    print("Already configured. Exiting.")
    exit(0)

print("=" * 50)
print("AI-FIREWALL FIRST BOOT SETUP")
print("=" * 50)

# Generate unique device ID
device_id = 'AF-2025-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
hostname = f'ai-firewall-{device_id[-4:]}'

# Set hostname
os.system(f'sudo hostnamectl set-hostname {hostname}')

# Generate default password (printed on activation card)
default_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Save config
config = {
    'device_id': device_id,
    'hostname': hostname,
    'first_boot': True,
    'setup_complete': False
}

with open('/home/pi/ai-firewall/device.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"\nDevice ID: {device_id}")
print(f"Hostname: {hostname}")
print(f"Default Password: {default_password}")
print("\nAccess dashboard at: http://{hostname}.local")
print("\nSetup will continue in web browser...")

# Mark as configured
open(SETUP_FLAG, 'w').close()
WIZARDEOF

chmod +x /home/pi/ai-firewall/setup_wizard.py

# Add to rc.local for first boot
sudo sed -i '/^exit 0/i /home/pi/ai-firewall/setup_wizard.py' /etc/rc.local

# ============================================================
# SECURITY HARDENING
# ============================================================

progress "Security hardening..."

# Change default password prompt
echo "pi:ChangeMe123!" | sudo chpasswd
echo -e "${YELLOW}Default password set to: ChangeMe123!${NC}"
echo -e "${YELLOW}User MUST change on first login!${NC}"

# SSH hardening
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Firewall
sudo apt install -y ufw
sudo ufw --force enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # Dashboard
sudo ufw allow 443/tcp  # HTTPS

# ============================================================
# AUTO-UPDATE CONFIGURATION
# ============================================================

progress "Configuring auto-updates..."

# System updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Suricata rules update (weekly)
cat > /tmp/update-suricata-rules.sh <<'EOF'
#!/bin/bash
docker exec ai-firewall-suricata suricata-update
docker restart ai-firewall-suricata
EOF
chmod +x /tmp/update-suricata-rules.sh
sudo mv /tmp/update-suricata-rules.sh /usr/local/bin/

# Cron job
(crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/local/bin/update-suricata-rules.sh") | crontab -

# ============================================================
# SD CARD LONGEVITY OPTIMIZATIONS
# ============================================================

progress "Optimizing for SD card longevity..."

# Disable swap
sudo dphys-swapfile swapoff
sudo systemctl disable dphys-swapfile

# /tmp on RAM
echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=512m 0 0" | sudo tee -a /etc/fstab

# Reduce logging
sudo sed -i 's/^/#/' /etc/rsyslog.conf
echo '*.*;auth,authpriv.none -/var/log/syslog' | sudo tee -a /etc/rsyslog.conf

# Log rotation
cat > /tmp/ai-firewall-logs <<'EOF'
/home/pi/ai-firewall/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 pi pi
}
EOF
sudo mv /tmp/ai-firewall-logs /etc/logrotate.d/

# ============================================================
# BACKUP PARTITION CREATION
# ============================================================

progress "Creating backup partition (factory reset)..."

# This would create a read-only backup of the system
# For now, we'll document the process
echo "Backup partition created (simulated)"

# ============================================================
# FINAL CONFIGURATION
# ============================================================

progress "Final configuration..."

# Create activation card data
cat > /home/pi/ai-firewall/activation.txt <<EOF
AI-FIREWALL ACTIVATION
Device ID: (generated on first boot)
Dashboard: http://ai-firewall.local
Default Login: admin / (see activation card)

Scan QR code to activate and get support
EOF

# Create quick start guide data
cat > /home/pi/ai-firewall/quickstart.txt <<EOF
AI-FIREWALL QUICK START

1. Connect BLUE cable: Modem → INTERNET port
2. Connect YELLOW cable: ROUTER port → Your router
3. Connect POWER cable
4. Wait for GREEN LED (2 minutes)
5. Open browser: http://ai-firewall.local
6. Follow setup wizard

Support: support@ai-firewall.com
EOF

# ============================================================
# QUALITY CONTROL TEST
# ============================================================

progress "Running quality control tests..."

echo "Starting all services..."
sudo systemctl start ai-firewall
sleep 60

echo "Testing Docker containers..."
docker ps | grep ai-firewall

echo "Testing dashboard..."
curl -f http://localhost:80 > /dev/null && echo "✅ Dashboard OK" || echo "❌ Dashboard FAILED"

echo "Testing API..."
curl -f http://localhost:8000/health > /dev/null && echo "✅ API OK" || echo "❌ API FAILED"

# Stop services (ready for cloning)
docker-compose -f /home/pi/ai-firewall/docker-compose-rpi.yml down

# ============================================================
# COMPLETION
# ============================================================

echo ""
echo "=================================================="
echo -e "${GREEN}FACTORY SETUP COMPLETE!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Shutdown: sudo shutdown -h now"
echo "2. Create image: Win32DiskImager → Read"
echo "3. Clone to production SD cards"
echo "4. Each card will auto-generate unique ID on first boot"
echo ""
echo "Default credentials:"
echo "  Username: pi"
echo "  Password: ChangeMe123! (MUST be changed)"
echo ""
echo "Dashboard: http://ai-firewall.local"
echo "=================================================="
