# Soma extreme cross-language benchmarks

This suite compares Soma programs with equivalent Python, JavaScript, Go, Rust, and C++ implementations. The published ranking is [docs/MEASURED_PERFORMANCE.md](../../docs/MEASURED_PERFORMANCE.md). The generated report for that run is [REPORT.md](REPORT.md).

## What is measured

Seventeen tasks: N-queens, Mandelbrot, matrix multiply, longest common subsequence, sieve, N-body, binary trees, breadth-first search, bottom-up mergesort, a 12-step stencil, a histogram, dense Dijkstra, Floyd-Warshall, zero-one knapsack, Levenshtein edit distance, longest increasing subsequence, and 12 steps of Conway's Life. Each task has three input sizes. Kernel time is measured inside the process. A zero-iteration run measures cold start. On Linux, GNU `time` records peak resident memory.

Every implementation prints a checksum. A timing is discarded if it times out, crashes, or disagrees with the Python reference. Fast runtimes repeat the kernel so the clock resolution does not dominate.

Soma in the default set is the native lowering: the `.sm` source is compiled to C++ and built with `g++ -O3 -std=c++20 -march=native`, the same class of flags as the C++ baseline. The Soma source stays the straightforward cells.

## Reproduce

The full suite needs Python, Node.js, Go, Rust, and a C++20 compiler:

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

The workflow `Extreme cross-language benchmarks` runs this on GitHub-hosted Ubuntu. Compare values inside one run. Runner hardware changes between runs.

Generated files in the output directory:

- `raw_results.json`: environment, builds, samples, and checksums.
- `REPORT.md`: the generated analysis for that output directory.

`results/` in the repository is only a note. The committed ranking is `docs/MEASURED_PERFORMANCE.md`.
