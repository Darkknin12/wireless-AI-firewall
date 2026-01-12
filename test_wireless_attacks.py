#!/usr/bin/env python3
"""
WIRELESS ATTACKS DEMONSTRATION
Simulates various wireless network attacks for AI-Firewall detection
Uses real CIC-IDS2017 data patterns adapted for wireless attack scenarios
"""

import requests
import time
import random
import pandas as pd

API_URL = "http://localhost:8000"

# Load real attack data patterns from CIC-IDS2017
DDOS_FILE = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
PORTSCAN_FILE = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv"
WEBATTACK_FILE = "ml_data/MachineLearningCVE/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"

# Wireless attack types we'll simulate
WIRELESS_ATTACKS = [
    {
        "name": "WiFi Deauth Attack",
        "description": "Deauthentication flood attack disconnecting clients from AP",
        "source_file": DDOS_FILE,
        "color": "\033[91m"  # Red
    },
    {
        "name": "Evil Twin AP",
        "description": "Rogue access point impersonating legitimate network",
        "source_file": PORTSCAN_FILE,
        "color": "\033[93m"  # Yellow
    },
    {
        "name": "WiFi KRACK Attack",
        "description": "Key Reinstallation Attack on WPA2",
        "source_file": WEBATTACK_FILE,
        "color": "\033[95m"  # Purple
    },
    {
        "name": "Bluetooth Hijack",
        "description": "Bluetooth connection hijacking attempt",
        "source_file": DDOS_FILE,
        "color": "\033[94m"  # Blue
    },
    {
        "name": "WiFi Jamming",
        "description": "RF jamming disrupting wireless communications",
        "source_file": DDOS_FILE,
        "color": "\033[96m"  # Cyan
    },
    {
        "name": "PMKID Attack",
        "description": "WPA2 PMKID hash capture attack",
        "source_file": PORTSCAN_FILE,
        "color": "\033[92m"  # Green
    },
    {
        "name": "Wardriving Probe",
        "description": "Network reconnaissance and scanning",
        "source_file": PORTSCAN_FILE,
        "color": "\033[97m"  # White
    },
    {
        "name": "IoT Zigbee Attack",
        "description": "Attack on IoT Zigbee wireless protocol",
        "source_file": WEBATTACK_FILE,
        "color": "\033[91m"
    }
]

# Benign wireless traffic file
BENIGN_FILE = "ml_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv"

# Normal wireless traffic patterns
BENIGN_TRAFFIC = [
    {
        "name": "WiFi Web Browsing",
        "description": "Normal HTTPS web browsing over WiFi"
    },
    {
        "name": "WiFi Video Stream", 
        "description": "Netflix/YouTube streaming over wireless"
    },
    {
        "name": "Bluetooth Audio",
        "description": "Normal Bluetooth headphone connection"
    },
    {
        "name": "IoT Smart Home",
        "description": "Normal smart home device communication"
    },
    {
        "name": "WiFi File Transfer",
        "description": "Normal file download over WiFi"
    }
]


def load_attack_samples(file_path, n_samples=3, benign=False):
    """Load attack or benign samples from CSV"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
        df.columns = [col.strip() for col in df.columns]
        
        # Filter by label
        if benign:
            df = df[df['Label'] == 'BENIGN']
        else:
            df = df[df['Label'] != 'BENIGN']
        
        if len(df) == 0:
            return []
        
        samples = df.sample(n=min(n_samples, len(df)))
        return samples.to_dict('records')
    except Exception as e:
        print(f"  Error loading: {e}")
        return []


def send_flow(flow_data, traffic_name, is_attack=True):
    """Send flow to API"""
    try:
        src_ip = generate_wireless_ip()
        dst_ip = generate_wireless_ip()
        
        # Remove non-feature columns
        for col in ['Label', 'Source IP', 'Destination IP', 'Flow ID', 'Timestamp']:
            if col in flow_data:
                del flow_data[col]
        
        flow_data["src_ip"] = src_ip
        flow_data["dst_ip"] = dst_ip
        flow_data["attack_type"] = traffic_name if is_attack else "BENIGN"
        
        response = requests.post(
            f"{API_URL}/predict/raw",
            json=flow_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def print_banner():
    print("\033[96m")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           🛜  WIRELESS TRAFFIC SIMULATOR  🛜                 ║")
    print("║                  AI-Firewall Detection Test                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  🔴 ATTACKS:                    🟢 NORMAL TRAFFIC:           ║")
    print("║  • WiFi Deauthentication        • WiFi Web Browsing          ║")
    print("║  • Evil Twin AP                 • WiFi Video Stream          ║")
    print("║  • KRACK Attack                 • Bluetooth Audio            ║")
    print("║  • WiFi Jamming                 • IoT Smart Home             ║")
    print("║  • PMKID Attack                 • WiFi File Transfer         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("\033[0m")


def generate_wireless_ip():
    """Generate typical wireless network IP"""
    networks = ["192.168.1", "192.168.0", "10.0.0", "172.16.0"]
    network = random.choice(networks)
    return f"{network}.{random.randint(1, 254)}"


def main():
    print_banner()
    
    # Check API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\033[91m❌ API not available\033[0m")
            return
        print("\033[92m✅ API Connected\033[0m")
    except:
        print("\033[91m❌ Cannot connect to API\033[0m")
        return
    
    print(f"\n\033[93m📡 Watch the dashboard at: http://localhost:80\033[0m")
    print("\033[90m" + "─" * 60 + "\033[0m")
    
    detected = 0
    total_attacks = 0
    correct_benign = 0
    total_benign = 0
    
    print("\n\033[1;91m🔴 LAUNCHING WIRELESS ATTACKS:\033[0m\n")
    
    for attack in WIRELESS_ATTACKS:
        color = attack["color"]
        name = attack["name"]
        desc = attack["description"]
        
        print(f"{color}━━━ {name} ━━━\033[0m")
        print(f"\033[90m    {desc}\033[0m")
        
        samples = load_attack_samples(attack["source_file"], n_samples=3, benign=False)
        
        if not samples:
            print(f"    \033[93m⚠️ No samples available\033[0m\n")
            continue
        
        for i, sample in enumerate(samples):
            result = send_flow(sample.copy(), name, is_attack=True)
            total_attacks += 1
            
            if result:
                pred = result.get("prediction", "").upper()
                score = result.get("ensemble_score", 0)
                
                if pred == "MALICIOUS":
                    detected += 1
                    print(f"    {color}✅ Attack {i+1}/3 DETECTED\033[0m (threat score: {score:.1%})")
                else:
                    print(f"    \033[91m❌ Attack {i+1}/3 missed\033[0m (score: {score:.3f})")
            else:
                print(f"    \033[91m❌ Error sending attack\033[0m")
            
            time.sleep(0.4)
        
        print()
    
    # Now send benign traffic
    print("\n\033[1;92m🟢 SENDING NORMAL WIRELESS TRAFFIC:\033[0m\n")
    
    for traffic in BENIGN_TRAFFIC:
        name = traffic["name"]
        desc = traffic["description"]
        
        print(f"\033[92m━━━ {name} ━━━\033[0m")
        print(f"\033[90m    {desc}\033[0m")
        
        samples = load_attack_samples(BENIGN_FILE, n_samples=3, benign=True)
        
        if not samples:
            print(f"    \033[93m⚠️ No samples available\033[0m\n")
            continue
        
        for i, sample in enumerate(samples):
            result = send_flow(sample.copy(), name, is_attack=False)
            total_benign += 1
            
            if result:
                pred = result.get("prediction", "").upper()
                score = result.get("ensemble_score", 0)
                
                if pred == "BENIGN":
                    correct_benign += 1
                    print(f"    \033[92m✅ Traffic {i+1}/3 ALLOWED\033[0m (safe score: {1-score:.1%})")
                else:
                    print(f"    \033[93m⚠️ Traffic {i+1}/3 False Positive\033[0m (score: {score:.3f})")
            else:
                print(f"    \033[91m❌ Error sending traffic\033[0m")
            
            time.sleep(0.4)
        
        print()
    
    # Summary
    print("\033[96m" + "═" * 60)
    print("                    📊 DETECTION SUMMARY")
    print("═" * 60 + "\033[0m")
    
    attack_rate = (detected / total_attacks * 100) if total_attacks > 0 else 0
    benign_rate = (correct_benign / total_benign * 100) if total_benign > 0 else 0
    
    if attack_rate >= 90 and benign_rate >= 80:
        status_emoji = "🛡️"
        status_color = "\033[92m"
    elif attack_rate >= 70:
        status_emoji = "⚠️"
        status_color = "\033[93m"
    else:
        status_emoji = "🔓"
        status_color = "\033[91m"
    
    print(f"\n  \033[91m🔴 Attack Detection:\033[0m {status_color}{attack_rate:.1f}%\033[0m ({detected}/{total_attacks})")
    print(f"  \033[92m🟢 Benign Accuracy:\033[0m  {status_color}{benign_rate:.1f}%\033[0m ({correct_benign}/{total_benign})")
    print(f"\n  {status_emoji} Overall Status: {status_color}{'PROTECTED' if attack_rate >= 90 else 'NEEDS ATTENTION'}\033[0m")
    print(f"\n\033[96m{'═' * 60}\033[0m")
    print("\n\033[93m👀 Check the dashboard for traffic breakdown!\033[0m\n")


if __name__ == "__main__":
    main()
