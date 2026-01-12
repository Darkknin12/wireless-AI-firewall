"""
Benchmark AI-Firewall Latency
Meet inference snelheid voor verschillende scenario's
"""

import time
import numpy as np
import pandas as pd
from inference import AIFirewallInference, create_example_flow
from utils import Logger

logger = Logger(__name__).logger

def benchmark_single_flow(firewall, n_iterations=100):
    """Benchmark single flow inference"""
    logger.info(f"Benchmarking single flow inference ({n_iterations} iterations)...")
    
    # Create example flow
    flow = create_example_flow()
    
    latencies = []
    
    # Warmup
    for _ in range(10):
        firewall.predict_single_flow(flow)
    
    # Actual benchmark
    for i in range(n_iterations):
        start = time.perf_counter()
        result = firewall.predict_single_flow(flow)
        end = time.perf_counter()
        
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)
    
    return latencies

def benchmark_batch(firewall, batch_sizes=[10, 100, 1000, 5000]):
    """Benchmark batch inference"""
    results = {}
    
    for batch_size in batch_sizes:
        logger.info(f"Benchmarking batch size: {batch_size}")
        
        # Create batch
        flows = [create_example_flow() for _ in range(batch_size)]
        df = pd.DataFrame(flows)
        
        # Warmup
        firewall.predict_batch(df)
        
        # Benchmark (3 runs)
        times = []
        for _ in range(3):
            start = time.perf_counter()
            firewall.predict_batch(df)
            end = time.perf_counter()
            times.append(end - start)
        
        avg_time = np.mean(times)
        throughput = batch_size / avg_time
        per_flow = (avg_time / batch_size) * 1000  # ms
        
        results[batch_size] = {
            'total_time_s': avg_time,
            'per_flow_ms': per_flow,
            'throughput_fps': throughput
        }
    
    return results

def print_results(single_latencies, batch_results):
    """Print benchmark results"""
    print("\n" + "="*70)
    print("AI-FIREWALL LATENCY BENCHMARK")
    print("="*70)
    
    # Single flow stats
    print("\n[SINGLE FLOW INFERENCE]")
    print("-" * 70)
    print(f"Iterations:        {len(single_latencies)}")
    print(f"Mean Latency:      {np.mean(single_latencies):.2f} ms")
    print(f"Median Latency:    {np.median(single_latencies):.2f} ms")
    print(f"Min Latency:       {np.min(single_latencies):.2f} ms")
    print(f"Max Latency:       {np.max(single_latencies):.2f} ms")
    print(f"Std Dev:           {np.std(single_latencies):.2f} ms")
    print(f"P95 Latency:       {np.percentile(single_latencies, 95):.2f} ms")
    print(f"P99 Latency:       {np.percentile(single_latencies, 99):.2f} ms")
    print(f"\nMax Throughput:    {1000 / np.mean(single_latencies):.0f} flows/sec")
    
    # Batch stats
    print("\n[BATCH INFERENCE]")
    print("-" * 70)
    print(f"{'Batch Size':<15} {'Total Time':<15} {'Per Flow':<15} {'Throughput'}")
    print("-" * 70)
    
    for batch_size, stats in batch_results.items():
        print(f"{batch_size:<15} "
              f"{stats['total_time_s']:<15.3f}s "
              f"{stats['per_flow_ms']:<15.2f}ms "
              f"{stats['throughput_fps']:.0f} flows/sec")
    
    # Recommendations
    print("\n[RECOMMENDATIONS]")
    print("-" * 70)
    
    avg_latency = np.mean(single_latencies)
    p99_latency = np.percentile(single_latencies, 99)
    
    if avg_latency < 10:
        print("[EXCELLENT] Latency < 10ms - Perfect voor real-time monitoring")
    elif avg_latency < 50:
        print("[GOOD] Latency < 50ms - Geschikt voor real-time monitoring")
    elif avg_latency < 100:
        print("[ACCEPTABLE] Latency < 100ms - Kan gebruikt worden voor monitoring")
    else:
        print("[SLOW] Latency > 100ms - Overweeg GPU of model optimalisatie")
    
    if p99_latency < 100:
        print("[OK] P99 < 100ms: Stabiele performance")
    else:
        print("[WARNING] P99 > 100ms: Performance variatie aanwezig")
    
    # Use cases
    print("\n[USE CASES BASED ON LATENCY]")
    print("-" * 70)
    
    max_single_fps = 1000 / avg_latency
    best_batch = max(batch_results.items(), key=lambda x: x[1]['throughput_fps'])
    
    print(f"Single Flow Mode:  Max {max_single_fps:.0f} flows/sec")
    print(f"Best Batch Mode:   {best_batch[1]['throughput_fps']:.0f} flows/sec "
          f"(batch size: {best_batch[0]})")
    
    print("\nRecommended deployment:")
    if max_single_fps > 100:
        print("  - Real-time alerting: [OK] Geschikt")
    else:
        print("  - Real-time alerting: [WARNING] Gebruik batch mode")
    
    if best_batch[1]['throughput_fps'] > 1000:
        print("  - High-traffic networks: [OK] Geschikt")
    else:
        print("  - High-traffic networks: [WARNING] Overweeg multi-instance")
    
    print("\n" + "="*70)

def main():
    """Run benchmarks"""
    print("Initializing AI-Firewall...")
    firewall = AIFirewallInference()
    
    print("\n[1] Running single flow benchmark...")
    single_latencies = benchmark_single_flow(firewall, n_iterations=100)
    
    print("\n[2] Running batch benchmarks...")
    batch_results = benchmark_batch(firewall, batch_sizes=[10, 100, 1000, 5000])
    
    print_results(single_latencies, batch_results)
    
    # Save results
    results_df = pd.DataFrame({
        'iteration': range(len(single_latencies)),
        'latency_ms': single_latencies
    })
    results_df.to_csv('output/latency_benchmark.csv', index=False)
    print(f"\nResults saved to: output/latency_benchmark.csv")

if __name__ == "__main__":
    main()
