#!/bin/bash
#
# AI-Firewall Auto-Start Script
# Plaats dit in: /home/pi/ai-firewall/start.sh
# chmod +x start.sh
#

echo "========================================="
echo "AI-FIREWALL AUTO-START"
echo "========================================="

# Wait for network
echo "[1/5] Waiting for network..."
sleep 10

# Check Docker
echo "[2/5] Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker not running!"
    exit 1
fi

# Navigate to project
cd /home/pi/ai-firewall

# Stop old containers
echo "[3/5] Stopping old containers..."
docker compose -f docker-compose-rpi.yml down 2>/dev/null

# Update Suricata rules
echo "[4/5] Updating Suricata rules..."
docker pull jasonish/suricata:latest

# Start stack
echo "[5/5] Starting AI-Firewall..."
docker compose -f docker-compose-rpi.yml up -d

# Wait for health checks
sleep 30

# Status
echo ""
echo "========================================="
echo "AI-FIREWALL STATUS"
echo "========================================="
docker compose -f docker-compose-rpi.yml ps

echo ""
echo "✅ AI-Firewall is running!"
echo "📊 Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "========================================="
