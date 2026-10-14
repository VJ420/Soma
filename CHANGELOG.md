# Changelog

Soma is the language. `.sm` is the usual extension. `.fc` still loads. The surface is one cell for values, functions, objects, and modules: no `self`, no `class`, no `return`. The tail expression is the result. Pipelines are `->`. `match` takes guards. `{name}` interpolates. `spawn` starts a block. `use` loads a module.

## 2026-10-14 — Windows CLR, measured on one laptop

`soma run` on Windows compiles with `csc.exe` from `C:\Windows\Microsoft.NET\Framework64\v4.0.30319` and runs on the CLR. No g++, no .NET SDK. `aot_engine/clr_compiler.py` emits C# 5 from the same analysis as the C++ lowering, plus integer truncating division, 32-bit remainders that fit, a hoisted `row * width` base, and a bit board for N-queens up to 27 columns. `--engine clr` and `emit-cs` select it. The build directory is `.soma-build/` next to the source.

The published ranking is still the C++ lowering on the AMD EPYC 9V45. The laptop numbers are a second table in [docs/MEASURED_PERFORMANCE.md](docs/MEASURED_PERFORMANCE.md). Machine: Intel Core i7-10510U. All checksums matched.

At the published sizes, against the languages installed there: geometric mean **70.3×** CPython 3.12 and **3.63×** Node 26. Node was faster on binary trees only.

At sizes past that ceiling, with a handwritten C# port on the same `csc.exe`: geometric mean **102×** CPython, **3.09×** Node, and **1.92×** handwritten C#. Soma was fastest of the four on 10 of 17 tasks. Matrix multiply at 256 was 1.99 ms against 331 ms for the handwritten triple loop. Floyd-Warshall at 240 was 83.4 ms against 38.9 ms of handwritten C#, because a product of two variables stays 64-bit. Binary trees at depth 20 were 1,395 ms against 284 ms of Node.

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
| `aot_engine/clr_compiler.py` | Windows CLR compiler |
| `aot_engine/native_compiler.py` | C++ compiler behind the published ranking |
| `examples/` | Programs, including the `.fc` demos |
| `std/` | Math, array, and string modules |
| `benchmarks/extreme/` | The ranking harness and its report |
| `benchmarks/archive/` | Older probes |
| `docs/` | Specification and the measured table |
| `tests/` | Unit tests |
