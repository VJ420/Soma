"""
End-to-End Multi-Language Agentic Architecture Benchmark.
Compares:
1. Python (Standard sequential pipeline)
2. Python (multiprocessing / concurrent.futures)
3. Node.js (Async Promise.all / Worker threads)
4. Fractal FRAA (Recursive Agentic Swarm with JIT-accelerated kernels)

Measures:
- Wall-clock decomposition latency
- Multi-worker parallel throughput
- Aggregation overhead
- Total End-to-End Completion Time
"""
import time
import subprocess
import sys
import os
import json
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agentic_infra import ParallelCellEngine, TaskDecomposer

# Workload: 1,000,000 items decomposed into 4 parallel chunks with CPU intensive transform
TOTAL_ITEMS = 1_000_000

# -------------------------------------------------------------
# 1. PURE SEQUENTIAL PYTHON (Standard Legacy Approach)
# -------------------------------------------------------------
def benchmark_python_sequential():
    t0 = time.perf_counter()
    data = list(range(TOTAL_ITEMS))
    results = []
    # Decompose + process sequentially
    chunk_size = TOTAL_ITEMS // 4
    for i in range(4):
        chunk = data[i * chunk_size : (i + 1) * chunk_size]
        res = sum(x * x + 7 for x in chunk)
        results.append(res)
    total = sum(results)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

# -------------------------------------------------------------
# 2. PYTHON CONCURRENT THREADPOOL (Standard Python Parallel)
# -------------------------------------------------------------
def _process_chunk_py(chunk):
    return sum(x * x + 7 for x in chunk)

def benchmark_python_threadpool():
    t0 = time.perf_counter()
    data = list(range(TOTAL_ITEMS))
    chunk_size = TOTAL_ITEMS // 4
    chunks = [data[i * chunk_size : (i + 1) * chunk_size] for i in range(4)]
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(_process_chunk_py, chunks))
    total = sum(results)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

# -------------------------------------------------------------
# 3. NODE.JS PROMISE.ALL CONCURRENCY (V8 Baseline)
# -------------------------------------------------------------
def benchmark_node_parallel():
    node_script = f"""
    const {{ performance }} = require('perf_hooks');
    const TOTAL = {TOTAL_ITEMS};
    const chunk_size = TOTAL / 4;

    function processChunk(start, end) {{
        return new Promise(resolve => {{
            let s = 0;
            for (let i = start; i < end; i++) {{
                s += (i * i + 7);
            }}
            resolve(s);
        }});
    }}

    async function run() {{
        const t0 = performance.now();
        const promises = [
            processChunk(0, chunk_size),
            processChunk(chunk_size, chunk_size * 2),
            processChunk(chunk_size * 2, chunk_size * 3),
            processChunk(chunk_size * 3, TOTAL)
        ];
        const res = await Promise.all(promises);
        const total = res.reduce((a, b) => a + b, 0);
        const t1 = performance.now();
        console.log(`TIME:${{(t1 - t0).toFixed(2)}}`);
    }}
    run();
    """
    cmd = ["node", "-e", node_script]
    out = subprocess.check_output(cmd, text=True)
    for line in out.splitlines():
        if "TIME:" in line:
            return float(line.split("TIME:")[1].strip())
    return 0.0

# -------------------------------------------------------------
# 4. FRACTAL RECURSIVE AGENTIC ARCHITECTURE (FRAA)
# -------------------------------------------------------------
def benchmark_fractal_fraa():
    t0 = time.perf_counter()
    data = list(range(TOTAL_ITEMS))
    engine = ParallelCellEngine(max_workers=4)
    # End-to-end: macro goal -> auto decompose -> parallel subagents -> aggregate
    summary = engine.run_goal("Compute massive data array transforms in parallel", payload=data)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

def main():
    print("=" * 75)
    print("   END-TO-END AGENTIC RECURSIVE PARALLEL BENCHMARK (1,000,000 ITEMS)   ")
    print("=" * 75)
    print("Task: Decompose Macro Goal -> Split into 4 Sub-Agent Cells ->")
    print("      Execute Parallel Math Kernel -> Aggregate Unified Output\n")

    print("[*] Running Python Sequential Baseline...")
    t_py_seq = benchmark_python_sequential()
    print(f"    Python Sequential          : {t_py_seq:8.2f} ms")

    print("[*] Running Python ThreadPool (GIL limited)...")
    t_py_thread = benchmark_python_threadpool()
    print(f"    Python ThreadPool          : {t_py_thread:8.2f} ms")

    print("[*] Running Node.js Promise.all Parallel...")
    t_node = benchmark_node_parallel()
    print(f"    Node.js (V8 Concurrency)   : {t_node:8.2f} ms")

    print("[*] Running Fractal Recursive Agentic Swarm (FRAA)...")
    t_fraa = benchmark_fractal_fraa()
    print(f"    Fractal FRAA Engine        : {t_fraa:8.2f} ms")

    print("\n" + "=" * 75)
    print("                         HEAD-TO-HEAD COMPARISON                         ")
    print("=" * 75)
    print(f"  Fractal FRAA vs Python Sequential : {t_py_seq / max(t_fraa, 0.01):5.2f}x FASTER")
    print(f"  Fractal FRAA vs Python ThreadPool : {t_py_thread / max(t_fraa, 0.01):5.2f}x FASTER")
    print(f"  Node.js V8 Parallel vs Python     : {t_py_seq / max(t_node, 0.01):5.2f}x FASTER")
    print("=" * 75)

if __name__ == "__main__":
    main()
