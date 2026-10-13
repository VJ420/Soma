"""
Benchmark Comparison:
Soma V1 Flat Swarm vs Soma V2 Hierarchical Swarm (Master -> Workers -> Micro-Assistants)
"""
import time
from swarm_v2_hierarchical import HierarchicalSwarmEngineV2

def main():
    print("=" * 84)
    print("      SOMA V2 SWARM EXPERIMENT: 3-TIER HIERARCHICAL DECOMPOSITION      ")
    print("=" * 84)

    total_items = 5_000_000
    print(f"Dataset Size: {total_items:,} compute elements\n")

    # 1. Level 1: Flat Swarm (1 Worker = Direct Execution)
    print("[Tier 1] Single Worker Baseline (No Assistants)...")
    t1 = HierarchicalSwarmEngineV2(num_workers=1, assistants_per_worker=1).execute_v8_jit_hierarchical(total_items)
    print(f"   -> Wall Time: {float(t1['duration_ms']):.2f} ms | Active Leaves: {t1['total_active_leaves']}")

    # 2. Level 2: Flat Multi-Worker (4 Workers, 1 Assistant each = 4 Leaves)
    print("\n[Tier 2] Flat Swarm (4 Workers, 1 Assistant each = 4 Leaves)...")
    t2 = HierarchicalSwarmEngineV2(num_workers=4, assistants_per_worker=1).execute_v8_jit_hierarchical(total_items)
    print(f"   -> Wall Time: {float(t2['duration_ms']):.2f} ms | Active Leaves: {t2['total_active_leaves']}")

    # 3. Level 3: Hierarchical Swarm (4 Workers x 4 Micro-Assistants = 16 Leaves)
    print("\n[Tier 3] Hierarchical Swarm (4 Workers x 4 Micro-Assistants = 16 Leaves)...")
    t3 = HierarchicalSwarmEngineV2(num_workers=4, assistants_per_worker=4).execute_v8_jit_hierarchical(total_items)
    print(f"   -> Wall Time: {float(t3['duration_ms']):.2f} ms | Active Leaves: {t3['total_active_leaves']}")

    # 4. Level 4: Ultra-Granular Hierarchical Swarm (8 Workers x 8 Micro-Assistants = 64 Leaves)
    print("\n[Tier 4] Ultra-Granular Hierarchical Swarm (8 Workers x 8 Micro-Assistants = 64 Leaves)...")
    t4 = HierarchicalSwarmEngineV2(num_workers=8, assistants_per_worker=8).execute_v8_jit_hierarchical(total_items)
    print(f"   -> Wall Time: {float(t4['duration_ms']):.2f} ms | Active Leaves: {t4['total_active_leaves']}")

    # 5. Level 5: High-Density Hierarchical Swarm (16 Workers x 16 Micro-Assistants = 256 Leaves)
    print("\n[Tier 5] High-Density Hierarchical Swarm (16 Workers x 16 Micro-Assistants = 256 Leaves)...")
    t5 = HierarchicalSwarmEngineV2(num_workers=16, assistants_per_worker=16).execute_v8_jit_hierarchical(total_items)
    print(f"   -> Wall Time: {float(t5['duration_ms']):.2f} ms | Active Leaves: {t5['total_active_leaves']}")

    # Mathematical Correctness Invariant
    assert t1['total_sum'] == t2['total_sum'] == t3['total_sum'] == t4['total_sum'] == t5['total_sum'], "Sums must match!"
    print("\n" + "=" * 84)
    print(f"  ALL 5 SWARM TIERS VERIFIED 100% IDENTICAL MATHEMATICAL RESULTS:")
    print(f"  Exact Sum: {t3['total_sum']}")
    print(f"  Speedup from Micro-Assistant Decomposition: {float(t1['duration_ms']) / float(t3['duration_ms']):.2f}x faster")
    print("=" * 84)

if __name__ == "__main__":
    main()
