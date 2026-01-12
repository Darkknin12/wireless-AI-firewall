#!/bin/bash

# ==========================================
# 🚀 AI-FIREWALL AUTO-INSTALLER (VM EDITION)
# ==========================================

# Kleuren voor output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (sudo bash install.sh)${NC}"
  exit
fi

echo -e "${GREEN}Starting AI-Firewall Installation...${NC}"

# 1. FIX DNS (Cruciaal voor Docker builds)
echo -e "${YELLOW}[1/7] Fixing DNS settings...${NC}"
rm -f /etc/resolv.conf
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf
echo -e "${GREEN}DNS fixed to Google DNS.${NC}"

# 2. SYSTEM UPDATE & DEPENDENCIES
echo -e "${YELLOW}[2/7] Updating system and installing dependencies...${NC}"
apt-get update
apt-get install -y curl git vim htop net-tools sed
echo -e "${GREEN}System updated.${NC}"

# 3. INSTALL DOCKER
echo -e "${YELLOW}[3/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $SUDO_USER
    echo -e "${GREEN}Docker installed.${NC}"
else
    echo -e "${GREEN}Docker already installed.${NC}"
fi

# 4. CONFIGURE NETWORK BRIDGE (Netplan)
echo -e "${YELLOW}[4/7] Configuring Network Bridge (br0)...${NC}"

# Disable Cloud-Init network management
echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg

# Backup old netplan configs
mkdir -p /etc/netplan/backup
mv /etc/netplan/*.yaml /etc/netplan/backup/ 2>/dev/null || true

# Create new Bridge Config
cat > /etc/netplan/01-bridge.yaml <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s3:
      dhcp4: no
      dhcp6: no
    enp0s8:
      dhcp4: no
      dhcp6: no
  bridges:
    br0:
      interfaces: [enp0s3, enp0s8]
      dhcp4: yes
      parameters:
        stp: no
        forward-delay: 0
EOF

echo -e "${GREEN}Netplan config created. (Will apply after reboot)${NC}"

# 5. CONFIGURE PROJECT FILES
echo -e "${YELLOW}[5/7] Configuring AI-Firewall settings...${NC}"

# Vervang eth0 met br0 in docker-compose-rpi.yml
if [ -f "docker-compose-rpi.yml" ]; then
    sed -i 's/-i eth0/-i br0/g' docker-compose-rpi.yml
    echo -e "${GREEN}Updated docker-compose-rpi.yml to use br0.${NC}"
else
    echo -e "${RED}Error: docker-compose-rpi.yml not found in current directory!${NC}"
fi

# Fix permissions
chown -R $SUDO_USER:$SUDO_USER .

# 6. CONFIGURE AUTO-START
echo -e "${YELLOW}[6/7] Configuring Auto-Start Service...${NC}"

CURRENT_DIR=$(pwd)
CURRENT_USER=$SUDO_USER

# Patch start.sh with correct path
sed -i "s|cd /home/pi/ai-firewall|cd $CURRENT_DIR|g" start.sh
# Patch start.sh to use 'docker compose' instead of 'docker-compose'
sed -i 's/docker-compose/docker compose/g' start.sh
chmod +x start.sh

# Patch ai-firewall.service with correct path and user
sed -i "s|User=pi|User=$CURRENT_USER|g" ai-firewall.service
sed -i "s|WorkingDirectory=/home/pi/ai-firewall|WorkingDirectory=$CURRENT_DIR|g" ai-firewall.service
sed -i "s|ExecStart=/home/pi/ai-firewall/start.sh|ExecStart=$CURRENT_DIR/start.sh|g" ai-firewall.service
sed -i "s|/home/pi/ai-firewall/docker-compose-rpi.yml|$CURRENT_DIR/docker-compose-rpi.yml|g" ai-firewall.service

# Install Service
cp ai-firewall.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ai-firewall

echo -e "${GREEN}Auto-start service installed and enabled.${NC}"

# 7. BUILD & START (Prepared)
echo -e "${YELLOW}[7/7] Preparing Docker containers...${NC}"

# We bouwen nog niet, want de bridge is nog niet actief.
# We maken een 'first-boot' script dat draait na de reboot.

cat > /root/first_boot.sh <<EOF
#!/bin/bash
echo "Waiting for network..."
sleep 10
cd $CURRENT_DIR
echo "Building containers (First Boot)..."
# Force build to ensure images exist for the service
docker compose -f docker-compose-rpi.yml up -d --build
echo "AI-Firewall is running!"
# Restart service to ensure it tracks the containers
systemctl restart ai-firewall
rm /root/first_boot.sh
EOF

chmod +x /root/first_boot.sh

# Add to crontab for one-time run
(crontab -l 2>/dev/null; echo "@reboot /root/first_boot.sh >> /var/log/ai-firewall-install.log 2>&1") | crontab -

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}==============================================${NC}"
echo -e "${YELLOW}The system needs to REBOOT to activate the Bridge.${NC}"
echo -e "${YELLOW}After reboot, Docker will automatically build and start.${NC}"
echo -e ""
echo -e "${RED}⚠️  REMINDER: Ensure 'Promiscuous Mode' is set to 'Allow All'${NC}"
echo -e "${RED}    in VirtualBox Network Settings for BOTH adapters!${NC}"
echo -e ""
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    netplan apply # Try to apply now just in case
    reboot
fi
