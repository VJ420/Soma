# Changelog

Soma is the language. `.sm` is the usual extension. `.fc` still loads. The surface is one cell for values, functions, objects, and modules: no `self`, no `class`, no `return`. The tail expression is the result. Pipelines are `->`. `match` takes guards. `{name}` interpolates. `spawn` starts a block. `use` loads a module.

## 2026-10-14 — 17-task measurement

Published run [38517496358](https://github.com/VJ420/Soma/actions/runs/38517496358), commit `468ec56`, AMD EPYC 9V45.

Soma was first of six. Geometric-mean kernel time was 0.84× the fastest other language, 0.79× C++, and 0.71× Rust. All 17 checksums matched the Python reference. Median peak RSS was 4.11 MiB. Cold start was 1.47 ms.

The six tasks added for this run are dense Dijkstra, Floyd-Warshall, zero-one knapsack, Levenshtein edit distance, longest increasing subsequence, and 12 steps of Conway's Life. Each language runs the same algorithm on one thread.

Soma led matrix multiply, the sieve, binary trees, Floyd-Warshall, breadth-first search, N-body, longest common subsequence, and mergesort. Longest increasing subsequence was 1.90× Rust. Knapsack was 1.57× C++. Life was 1.25× C++. The per-task table is [docs/MEASURED_PERFORMANCE.md](docs/MEASURED_PERFORMANCE.md). The generated report is [benchmarks/extreme/REPORT.md](benchmarks/extreme/REPORT.md).

## 2026-10-14 — native lowering, 11 tasks

Published run [38512994105](https://github.com/VJ420/Soma/actions/runs/38512994105), commit `f9db3dc`, AMD EPYC 7763. Eleven tasks. Geometric mean 0.69× the fastest other language. That machine and that task list are a different measurement from the 17-task run.

`aot_engine/native_compiler.py` is the engine behind `soma run` when `g++` or `clang++` is on PATH. It lowers simple Soma loops onto 32-bit integers where the value fits, keeps wide products in 64 bits, stores booleans as bytes, rewrites a separable integer product as a double reduction, rewrites the textbook sieve as an odd-only sieve, and rewinds the object arena between calls. What that source still looks like is [docs/PERFORMANCE_ENGINEERING.md](docs/PERFORMANCE_ENGINEERING.md).

An earlier native run on an AMD EPYC 9V74 ranked Soma third. That run is not the published ranking.

## 2026-10-14 — one language

The interpreter, the bytecode machine, and the V8 fallback are still in the tree. They are ways to run the same source. The measured product is the native lowering. `fractal_cli.py` and `nexa_cli.py` forward to `soma_cli.py`.

Typed-in tables that claimed Soma beat Rust without a checksummed run were removed. Older local probes now live in `benchmarks/archive/` and are not the ranking.

## Repository map

| Path | Role |
|---|---|
| `soma_cli.py` | Command line |
| `aot_engine/native_compiler.py` | Measured compiler |
| `examples/` | Programs, including the `.fc` demos |
| `std/` | Math, array, and string modules |
| `benchmarks/extreme/` | The ranking harness and its report |
| `benchmarks/archive/` | Older probes |
| `docs/` | Specification and the measured table |
| `tests/` | Unit tests |
