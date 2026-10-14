"""Archived local probe. The published ranking is docs/MEASURED_PERFORMANCE.md.

Full End-to-End Multi-Language Benchmark Suite.
Compares Python 3.12 (Sequential & Multi-Core), Node.js V8, and Fractal's Parallel Swarm Core.
"""
import time
import subprocess
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from swarm_core import BlazingSwarmEngine

TOTAL_ITEMS = 5_000_000  # 5 Million items to stress CPU cores

def py_sequential():
    t0 = time.perf_counter()
    total = 0
    for i in range(TOTAL_ITEMS):
        total += (i * i + 7)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

def node_raw():
    script = f"""
    const {{ performance }} = require('perf_hooks');
    const TOTAL = {TOTAL_ITEMS};
    const t0 = performance.now();
    let total = 0;
    for (let i = 0; i < TOTAL; i++) {{
        total += (i * i + 7);
    }}
    const t1 = performance.now();
    console.log((t1 - t0).toFixed(2));
    """
    out = subprocess.check_output(["node", "-e", script], text=True)
    return float(out.strip())

def main():
    print("=" * 75)
    print("      END-TO-END PARALLEL ARCHITECTURE BENCHMARK (5,000,000 ITEMS)      ")
    print("=" * 75)
    print("Workload: 5 Million Items decomposed into 4 Sub-Agent Cells & computed\n")

    print("[*] 1. Python 3.12 (Standard Sequential Baseline)...")
    t_py = py_sequential()
    print(f"    Python 3.12 (CPython Single Thread) : {t_py:8.2f} ms")

    print("[*] 2. Node.js (V8 JIT Baseline)...")
    t_node = node_raw()
    print(f"    Node.js (Google V8 Engine)          : {t_node:8.2f} ms")

    swarm = BlazingSwarmEngine(num_workers=4)

    print("[*] 3. Fractal JIT Parallel Swarm Core (FRAA)...")
    jit_res = swarm.execute_jit_swarm(TOTAL_ITEMS)
    t_jit = jit_res["wall_time_ms"]
    print(f"    Fractal JIT Parallel Swarm          : {t_jit:8.2f} ms")

    print("\n" + "=" * 75)
    print("                          FINAL HEAD-TO-HEAD STATS                       ")
    print("=" * 75)
    print(f"  * Fractal Swarm vs Python 3.12        : {t_py / t_jit:.1f}x FASTER")
    print(f"  * Fractal Swarm vs Node.js            : {t_node / t_jit:.1f}x FASTER")
    print(f"  * Time to process 5,000,000 items     : Python: {t_py:.1f}ms | Node: {t_node:.1f}ms | Fractal: {t_jit:.1f}ms")
    print("=" * 75)

if __name__ == "__main__":
    main()
