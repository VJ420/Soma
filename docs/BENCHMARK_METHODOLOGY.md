# Soma Multi-Language Benchmark Suite & Validation Methodology

**Conceived and Crafted in India**  
Created & Designed by **[Vighnesh Jha](https://github.com/VJ420)** ([@VJ420](https://github.com/VJ420))  
**Empirical Target:** Verifiable comparisons against Python 3.12, Go 1.22, and Rust Native Opt 3.

---

## 1. Benchmarking Philosophy & Engineering Invariants

Benchmark credibility requires strict adherence to reproducible scientific conditions:
1. **Zero Cold-Start Distortion**: JIT compilers undergo warm-up iterations before recording measurements.
2. **High-Resolution Clocks**: Runtimes are captured via sub-microsecond system timers (`time.perf_counter()` in Python, `performance.now()` in Node/V8, `std::chrono::high_resolution_clock` in C++).
3. **Identical Computational Invariants**:
   - Equivalent algorithmic Big-O complexities ($O(N)$ to $O(N^3)$).
   - Identical data types (64-bit IEEE-754 floating-point coordinates).
   - Equal sample sizes across all runs.
4. **Deterministic Seed Values**: Pseudo-random generators utilize fixed LCG constants (`seed = 123456789`) ensuring 1:1 mathematical equivalence across language outputs.

---

## 2. Benchmark Suite Inventory

The Fractal benchmark directory contains automated harnesses:

- [`benchmarks/hard_math_benchmark.py`](file:///C:/Users/vishu/.gemini/antigravity/scratch/fractal-lang/benchmarks/hard_math_benchmark.py): 7 extreme mathematical workloads.
- [`benchmarks/run_domain_benchmarks.py`](file:///C:/Users/vishu/.gemini/antigravity/scratch/fractal-lang/benchmarks/run_domain_benchmarks.py): 6 domain workloads (Fibonacci, Mandelbrot, MatMul, Monte Carlo, Swarm Parallelism, Hash lookups).
- [`benchmarks/e2e_full_benchmark.py`](file:///C:/Users/vishu/.gemini/antigravity/scratch/fractal-lang/benchmarks/e2e_full_benchmark.py): End-to-end multi-tier pipeline execution.

---

## 3. How to Reproduce Benchmarks

### Executing the Extreme Math Suite
```powershell
python benchmarks/hard_math_benchmark.py
```

### Inspecting Output JSON Results
```powershell
Get-Content benchmarks/hard_math_results.json | ConvertFrom-Json
```

### Running the Domain Benchmark Suite
```powershell
python benchmarks/run_domain_benchmarks.py
```
