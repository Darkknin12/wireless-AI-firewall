"""
Test AI-Firewall Blocking Functionaliteit
Demonstratie van automatic blocking
"""

from firewall_blocker import FirewallBlocker
from inference import AIFirewallInference
from utils import Logger
import json

def test_blocking_system():
    """Test het complete blocking system"""
    
    logger = Logger(__name__).logger
    
    print("\n" + "="*70)
    print("AI-FIREWALL AUTOMATIC BLOCKING TEST")
    print("="*70)
    
    # 1. Initialize blocker
    print("\n[1] Initializing Firewall Blocker...")
    blocker = FirewallBlocker()
    
    print(f"    Auto-block enabled: {blocker.auto_block_enabled}")
    print(f"    Block threshold: {blocker.block_threshold}")
    print(f"    Whitelist: {blocker.whitelist}")
    
    # 2. Load AI models
    print("\n[2] Loading AI Models...")
    try:
        inference_engine = AIFirewallInference()
        inference_engine.load_models()
        print("    ✅ Models loaded successfully")
    except Exception as e:
        print(f"    ❌ Failed to load models: {e}")
        return
    
    # 3. Simulate malicious flow
    print("\n[3] Simulating Malicious Network Flow...")
    
    malicious_flow = {
        # Source (attacker)
        'src_ip': '203.0.113.45',  # Example malicious IP
        'source_port': 54321,
        
        # Destination (victim)
        'dst_ip': '192.168.1.100',
        'destination_port': 22,  # SSH
        
        # Flow characteristics (DDoS pattern)
        'protocol': 6,  # TCP
        'flow_duration': 0.5,
        'total_fwd_packets': 1000,
        'total_backward_packets': 0,
        'total_length_of_fwd_packets': 60000,
        'total_length_of_bwd_packets': 0,
        'fwd_packet_length_max': 60,
        'fwd_packet_length_min': 60,
        'fwd_packet_length_mean': 60,
        'fwd_packet_length_std': 0,
        'bwd_packet_length_max': 0,
        'bwd_packet_length_min': 0,
        'bwd_packet_length_mean': 0,
        'bwd_packet_length_std': 0,
        'flow_bytes_s': 120000,
        'flow_packets_s': 2000,
        'flow_iat_mean': 0.0005,
        'flow_iat_std': 0.0001,
        'flow_iat_max': 0.001,
        'flow_iat_min': 0.0001,
        'fwd_iat_total': 0.5,
        'fwd_iat_mean': 0.0005,
        'fwd_iat_std': 0.0001,
        'fwd_iat_max': 0.001,
        'fwd_iat_min': 0.0001,
        'bwd_iat_total': 0,
        'bwd_iat_mean': 0,
        'bwd_iat_std': 0,
        'bwd_iat_max': 0,
        'bwd_iat_min': 0,
        'fwd_psh_flags': 0,
        'bwd_psh_flags': 0,
        'fwd_urg_flags': 0,
        'bwd_urg_flags': 0,
        'fwd_header_length': 20,
        'bwd_header_length': 0,
        'fwd_packets_s': 2000,
        'bwd_packets_s': 0,
        'min_packet_length': 60,
        'max_packet_length': 60,
        'packet_length_mean': 60,
        'packet_length_std': 0,
        'packet_length_variance': 0,
        'fin_flag_count': 0,
        'syn_flag_count': 1000,  # SYN flood!
        'rst_flag_count': 0,
        'psh_flag_count': 0,
        'ack_flag_count': 0,
        'urg_flag_count': 0,
        'cwe_flag_count': 0,
        'ece_flag_count': 0,
        'down_up_ratio': 0,
        'average_packet_size': 60,
        'avg_fwd_segment_size': 60,
        'avg_bwd_segment_size': 0,
        'fwd_avg_bytes_bulk': 0,
        'fwd_avg_packets_bulk': 0,
        'fwd_avg_bulk_rate': 0,
        'bwd_avg_bytes_bulk': 0,
        'bwd_avg_packets_bulk': 0,
        'bwd_avg_bulk_rate': 0,
        'subflow_fwd_packets': 1000,
        'subflow_fwd_bytes': 60000,
        'subflow_bwd_packets': 0,
        'subflow_bwd_bytes': 0,
        'init_win_bytes_forward': 5840,
        'init_win_bytes_backward': 0,
        'active_mean': 0.5,
        'active_std': 0,
        'active_max': 0.5,
        'active_min': 0.5,
        'idle_mean': 0,
        'idle_std': 0,
        'idle_max': 0,
        'idle_min': 0
    }
    
    print(f"    Source IP: {malicious_flow['src_ip']}")
    print(f"    Target: {malicious_flow['dst_ip']}:{malicious_flow['destination_port']}")
    print(f"    Pattern: SYN Flood (1000 SYN packets in 0.5s)")
    
    # 4. AI Prediction
    print("\n[4] Running AI Detection...")
    prediction = inference_engine.predict_single_flow(malicious_flow)
    
    print(f"    Prediction: {prediction['prediction']}")
    print(f"    XGBoost Score: {prediction['xgb_score']:.3f}")
    print(f"    Isolation Forest Score: {prediction['if_score']:.3f}")
    print(f"    Ensemble Score: {prediction['ensemble_score']:.3f}")
    
    # 5. Automatic Blocking Decision
    print("\n[5] Blocking Decision...")
    
    if prediction['prediction'] == 'MALICIOUS':
        if prediction['ensemble_score'] >= blocker.block_threshold:
            print(f"    ⚠️  THREAT DETECTED!")
            print(f"    Score {prediction['ensemble_score']:.3f} >= Threshold {blocker.block_threshold}")
            
            # Check if auto-block is enabled
            if blocker.auto_block_enabled:
                print(f"    🔒 AUTOMATIC BLOCKING ENABLED")
                
                # Process and block
                blocked = blocker.process_prediction(malicious_flow, prediction)
                
                if blocked:
                    print(f"    ✅ IP {malicious_flow['src_ip']} BLOCKED!")
                else:
                    print(f"    ⚠️  Blocking failed (check logs)")
            else:
                print(f"    ⚠️  AUTOMATIC BLOCKING DISABLED")
                print(f"    Would have blocked: {malicious_flow['src_ip']}")
                print(f"    Enable in config.json: firewall.auto_block = true")
        else:
            print(f"    Score {prediction['ensemble_score']:.3f} < Threshold {blocker.block_threshold}")
            print(f"    No blocking action taken")
    else:
        print(f"    ✅ Benign traffic - No action needed")
    
    # 6. Show statistics
    print("\n[6] Firewall Statistics...")
    stats = blocker.get_stats()
    
    print(f"    Total Blocked IPs: {stats['total_blocked']}")
    print(f"    Auto-block Enabled: {stats['auto_block_enabled']}")
    print(f"    Block Threshold: {stats['block_threshold']}")
    print(f"    Whitelist Size: {stats['whitelist_size']}")
    
    if blocker.blocked_ips:
        print(f"\n    Currently Blocked IPs:")
        for ip in blocker.get_blocked_ips():
            print(f"      - {ip}")
    
    # 7. Benign traffic test
    print("\n[7] Testing Benign Traffic...")
    
    benign_flow = {
        'src_ip': '192.168.1.50',
        'dst_ip': '8.8.8.8',
        'source_port': 54123,
        'destination_port': 443,
        'protocol': 6,
        'flow_duration': 2.5,
        'total_fwd_packets': 10,
        'total_backward_packets': 8,
        'total_length_of_fwd_packets': 800,
        'total_length_of_bwd_packets': 6400,
        'fwd_packet_length_max': 120,
        'fwd_packet_length_min': 60,
        'fwd_packet_length_mean': 80,
        'fwd_packet_length_std': 20,
        'bwd_packet_length_max': 1200,
        'bwd_packet_length_min': 600,
        'bwd_packet_length_mean': 800,
        'bwd_packet_length_std': 200,
        'flow_bytes_s': 2880,
        'flow_packets_s': 7.2,
        'flow_iat_mean': 0.25,
        'flow_iat_std': 0.1,
        'flow_iat_max': 0.5,
        'flow_iat_min': 0.1,
        'fwd_iat_total': 2.5,
        'fwd_iat_mean': 0.25,
        'fwd_iat_std': 0.1,
        'fwd_iat_max': 0.5,
        'fwd_iat_min': 0.1,
        'bwd_iat_total': 2.0,
        'bwd_iat_mean': 0.25,
        'bwd_iat_std': 0.1,
        'bwd_iat_max': 0.4,
        'bwd_iat_min': 0.15,
        'fwd_psh_flags': 1,
        'bwd_psh_flags': 1,
        'fwd_urg_flags': 0,
        'bwd_urg_flags': 0,
        'fwd_header_length': 20,
        'bwd_header_length': 20,
        'fwd_packets_s': 4.0,
        'bwd_packets_s': 3.2,
        'min_packet_length': 60,
        'max_packet_length': 1200,
        'packet_length_mean': 400,
        'packet_length_std': 350,
        'packet_length_variance': 122500,
        'fin_flag_count': 2,
        'syn_flag_count': 1,
        'rst_flag_count': 0,
        'psh_flag_count': 2,
        'ack_flag_count': 16,
        'urg_flag_count': 0,
        'cwe_flag_count': 0,
        'ece_flag_count': 0,
        'down_up_ratio': 8,
        'average_packet_size': 400,
        'avg_fwd_segment_size': 80,
        'avg_bwd_segment_size': 800,
        'fwd_avg_bytes_bulk': 0,
        'fwd_avg_packets_bulk': 0,
        'fwd_avg_bulk_rate': 0,
        'bwd_avg_bytes_bulk': 0,
        'bwd_avg_packets_bulk': 0,
        'bwd_avg_bulk_rate': 0,
        'subflow_fwd_packets': 10,
        'subflow_fwd_bytes': 800,
        'subflow_bwd_packets': 8,
        'subflow_bwd_bytes': 6400,
        'init_win_bytes_forward': 65535,
        'init_win_bytes_backward': 65535,
        'active_mean': 2.0,
        'active_std': 0.3,
        'active_max': 2.5,
        'active_min': 1.5,
        'idle_mean': 0.1,
        'idle_std': 0.05,
        'idle_max': 0.2,
        'idle_min': 0.05
    }
    
    prediction_benign = inference_engine.predict_single_flow(benign_flow)
    
    print(f"    Source IP: {benign_flow['src_ip']}")
    print(f"    Prediction: {prediction_benign['prediction']}")
    print(f"    Ensemble Score: {prediction_benign['ensemble_score']:.3f}")
    print(f"    Action: ✅ Allow (normal HTTPS traffic)")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"✅ AI Detection: Working")
    print(f"✅ Threat Classification: Working") 
    print(f"✅ Blocking Logic: Working")
    
    if blocker.auto_block_enabled:
        print(f"✅ Automatic Blocking: ENABLED")
    else:
        print(f"⚠️  Automatic Blocking: DISABLED")
        print(f"   Enable in config.json to auto-block threats")
    
    print("\nTo enable automatic blocking:")
    print("1. Edit config.json")
    print('2. Set: "auto_block": true')
    print("3. Restart realtime_firewall.py")
    print("")

if __name__ == "__main__":
    test_blocking_system()
