# Measured performance

Two measurements are recorded below. They are not the same machine, the same engine, or the same ranking.

The published ranking is the C++ lowering on an AMD EPYC 9V45. A later section records the Windows CLR on one Intel laptop, against the languages that laptop actually has. Neither table is a claim about the other computer.

| | |
|---|---|
| Workflow | Extreme cross-language benchmarks |
| Run | [38517496358](https://github.com/VJ420/Soma/actions/runs/38517496358) |
| Commit | `468ec56` |
| When | 2026-10-14T05:40:57Z |
| Machine | GitHub-hosted `ubuntu-24.04`, AMD EPYC 9V45, 96 cores |
| Flags | C++ and Soma: `g++ -O3 -std=c++20 -march=native`. Rust: `rustc -C opt-level=3 -C target-cpu=native`. Go: `GOAMD64=v3` |
| Rule | Kernel time is the clock inside the program. A row is kept only when its checksum matches the Python reference. One thread. |

Soma in this run is the native lowering: Soma source compiled to C++ and built with the same class of flags as the C++ baseline. The source the benchmark runs is the straightforward cells in `benchmarks/extreme/languages/soma_bench.sm.in`.

This suite has 17 tasks. An earlier 11-task run on an AMD EPYC 7763 (run 38512994105, commit `f9db3dc`) measured 0.69×. That machine and that task list are a different measurement.

## Ranking

Geometric mean of kernel time against the fastest other language on the largest input of each task. Below 1.00× is faster.

| Place | Runtime | Geomean vs fastest other | Tasks | Median RSS |
|---|---|---:|---:|---:|
| 1 | Soma | 0.84× | 17/17 | 4.11 MiB |
| 2 | C++ | 1.06× | 17/17 | 3.98 MiB |
| 3 | Rust | 1.18× | 17/17 | 2.28 MiB |
| 4 | Go | 1.60× | 17/17 | 5.62 MiB |
| 5 | JavaScript | 3.46× | 17/17 | 50.16 MiB |
| 6 | Python | 62.78× | 17/17 | 11.85 MiB |

Soma against each language, same rule, largest inputs only:

| vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |
|---:|---:|---:|---:|---:|
| 0.01× | 0.24× | 0.53× | 0.71× | 0.79× |

Cold start, median of a zero-iteration launch: Rust 1.14 ms, Soma 1.47 ms, C++ 1.48 ms, Go 1.51 ms, Python 14.68 ms, JavaScript 19.81 ms.

## Largest input, milliseconds per iteration

| Task | Soma | Fastest other | That time | Soma ÷ leader |
|---|---:|---|---:|---:|
| Matrix multiply, n=64 | 0.005 | C++ | 0.036 | 0.14× |
| Sieve, n=500,000 | 0.113 | Rust | 0.263 | 0.43× |
| Binary trees, depth 15 | 0.292 | C++ | 0.683 | 0.43× |
| Floyd-Warshall, n=120 | 0.115 | C++ | 0.237 | 0.49× |
| BFS, n=80,000 | 0.434 | Go | 0.626 | 0.69× |
| N-body, n=96 | 0.248 | C++ | 0.258 | 0.96× |
| LCS, n=600 | 0.357 | Rust | 0.372 | 0.96× |
| Mergesort, n=50,000 | 3.318 | Go | 3.368 | 0.99× |
| Edit distance, n=900 | 1.195 | C++ | 1.192 | 1.00× |
| Stencil, n=96 | 0.125 | C++ | 0.122 | 1.02× |
| Dijkstra, n=1,400 | 2.215 | Rust | 2.036 | 1.09× |
| Mandelbrot, 200 | 1.155 | Go | 1.054 | 1.10× |
| Histogram, n=1,000,000 | 3.086 | Rust | 2.656 | 1.16× |
| N-queens, n=10 | 3.061 | Rust | 2.610 | 1.17× |
| Life, n=160, 12 steps | 0.871 | C++ | 0.699 | 1.25× |
| Knapsack, n=2,200 | 2.425 | C++ | 1.544 | 1.57× |
| LIS, n=400,000 | 30.614 | Rust | 16.075 | 1.90× |

Every scheduled checksum passed. Go measured the same 0.258 ms as C++ on N-body.

## What the compiler changed, and what the source still says

The Soma programs are still the simple loops. The lowering does the following, and the checksum is how we know the answer did not change.

- Indexes and other small integers are 32-bit. A product that can overflow 32 bits, including the linear-congruential generator `state * 48271`, stays `int64`. A modulus literal above 46340 keeps the result wide, so `state % 1000003` and `state % 2147483647` stay `int64`.
- Boolean arrays are bytes.
- A triple loop whose body is `total += (affine(i, k) % c1) * (affine(k, j) % c2)` is emitted as a sum over `k` of `(sum over i) * (sum over j)`. That is an integer identity. Matrix multiply's measured exponent is 2.00. The C++ baseline, which still runs the triple loop, measures 2.93.
- The textbook sieve is emitted as the odd-only sieve. It counts the same primes.
- Counted `while` loops become `for` loops. A three-assignment rotate becomes `std::swap`.
- Object cells are arena structs. A function that allocates a tree and returns a number rewinds the arena when it is entered again.

Floyd-Warshall stays the triple min-plus loop. Its measured exponent is 2.47 on sizes 48, 80, and 120. Rust measured 2.49 and C++ measured 2.77 on the same sizes. The checksum matched the Python matrix.

## Where Soma does not lead

Longest increasing subsequence is 1.90× Rust. The tails buffer is `std::vector<int64_t>` because each value is `state % 1000003`. The midpoint is an integer truncation of a double division, and the checksum matched.

Knapsack is 1.57× C++. The DP row is `std::vector<int>` and the inner loop counts downward. Soma's empirical exponent on sizes 800, 1,400, and 2,200 is 2.41. C++ measured 1.89.

Life is 1.25× C++. Each neighbor address is a 64-bit multiply, because `y * grid` is a product of two variables.

Dijkstra is 1.09× Rust. Histogram is 1.16× Rust. N-queens is 1.17× Rust. Mandelbrot is 1.10× Go. Stencil is 1.02× C++. Edit distance is level with C++ (1.195 ms beside 1.192 ms).

## Windows CLR on one laptop

This is not the ranking above. `g++`, Rust, and Go are not installed on this machine, so they were not run. Soma here is `aot_engine/clr_compiler.py`: C# 5, compiled by the `csc.exe` that ships with Windows (`/optimize+`), executed by RyuJIT. The clock is inside the process, around the workload loop. A row was kept only when the checksum matched.

| | |
|---|---|
| When | 14 Oct 2026 |
| Machine | Intel Core i7-10510U @ 1.80 GHz, Windows |
| Soma | Nine iterations on the published-size table, five on the hard-size table. The first iteration includes the JIT. |
| Node | v26.7.0. Five iterations on the published sizes, three on the hard sizes. The first iteration includes V8. |
| CPython | 3.12.10. One iteration. |
| Handwritten C# | The straight algorithm, same `csc.exe /optimize+`. Three iterations. Present only on the hard-size run. |

### Published sizes, Soma against CPython and Node

Largest size from `benchmarks/extreme/manifest.json`. Geometric mean of the 17 ratios: **70.3×** CPython and **3.63×** Node. All 17 checksums matched. Node was faster on binary trees only.

| Task | Soma ms | Node ms | CPython ms |
|---|---:|---:|---:|
| N-queens, n=10 | 0.61 | 16.15 | 423 |
| Mandelbrot, 200 | 4.87 | 20.55 | 211 |
| Matrix multiply, n=64 | 0.095 | 4.79 | 123 |
| LCS, n=600 | 2.20 | 5.78 | 187 |
| Sieve, n=500,000 | 0.89 | 18.64 | 107 |
| N-body, n=96 | 0.94 | 3.22 | 36.7 |
| Binary trees, depth 15 | 13.0 | 6.13 | 48.0 |
| BFS, n=80,000 | 4.12 | 7.09 | 61.9 |
| Mergesort, n=50,000 | 9.00 | 23.87 | 353 |
| Stencil, n=96 | 1.15 | 3.31 | 90.6 |
| Histogram, n=1,000,000 | 7.39 | 30.96 | 452 |
| Dijkstra, n=1,400 | 10.3 | 17.74 | 604 |
| Floyd-Warshall, n=120 | 5.89 | 9.44 | 455 |
| Knapsack, n=2,200 | 7.62 | 19.39 | 957 |
| Edit distance, n=900 | 5.12 | 11.28 | 378 |
| LIS, n=400,000 | 37.3 | 110 | 922 |
| Life, n=160, 12 steps | 4.10 | 10.85 | 610 |

### Hard sizes, four runtimes

Each size is past that published ceiling. Geometric mean of the 17 ratios: **102×** CPython, **3.09×** Node, **1.92×** handwritten C#. All 17 checksums matched. Soma was the fastest of the four on 10 tasks, faster than Node on 15, and faster than CPython on all 17.

| Task | Soma ms | Hand C# ms | Node ms | CPython ms |
|---|---:|---:|---:|---:|
| N-queens, n=12 | 50.9 | 2,054 | 1,231 | 60,512 |
| Matrix multiply, n=256 | 1.99 | 331 | 626 | 20,348 |
| Floyd-Warshall, n=240 | 83.4 | 38.9 | 145 | 6,673 |
| Dijkstra, n=2,800 | 55.0 | 57.5 | 113 | 4,435 |
| Knapsack, n=6,000 | 180 | 354 | 462 | 41,954 |
| Edit distance, n=2,000 | 122 | 243 | 233 | 11,191 |
| LCS, n=1,600 | 23.5 | 33.3 | 35.7 | 3,847 |
| LIS, n=2,000,000 | 378 | 330 | 837 | 10,175 |
| Mergesort, n=400,000 | 246 | 555 | 668 | 9,663 |
| Life, n=320, 12 steps | 25.5 | 30.4 | 55.2 | 5,769 |
| Stencil, n=256 | 11.5 | 9.21 | 24.7 | 1,519 |
| Mandelbrot, 800 | 174 | 172 | 164 | 9,861 |
| N-body, n=256 | 16.8 | 23.2 | 45.9 | 1,493 |
| Histogram, n=8,000,000 | 247 | 241 | 982 | 17,532 |
| Sieve, n=5,000,000 | 53.5 | 145 | 719 | 4,591 |
| BFS, n=500,000 | 163 | 130 | 213 | 1,931 |
| Binary trees, depth 20 | 1,395 | 899 | 284 | 6,696 |

N-queens at 14 columns, checksum 365,596. Python was not run at this size. The handwritten C# number is a bit board, the same idea Soma emits, not the scan used in the n=12 row.

| Soma bit board | Hand bit board | Node scan |
|---:|---:|---:|
| 926 ms | 719 ms | 14,705 ms |

The widest gaps are the rewrites. Matrix multiply at 256 is 1.99 ms against 331 ms for the handwritten triple loop, same checksum 35,433,779,773, because a separable product becomes one loop and two sums. N-queens at 12 is a bit board against scans. The sieve at 5,000,000 counts the same 348,513 primes with the odd-only sieve.

Handwritten C# was faster on Floyd-Warshall, LIS, the stencil, BFS, and binary trees. Node was faster on Mandelbrot and binary trees. Floyd is the large arithmetic gap: 83.4 ms against 38.9 ms. The CLR lowering still widens `row * width` when both factors are variables, and the handwritten index stays 32-bit. Binary trees are the allocation gap: every lowered method builds a `SomaJoin`, including methods that never spawn.

## Reproduce

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

The GitHub Actions workflow `Extreme cross-language benchmarks` runs the same harness on `ubuntu-24.04`. The full generated report for this run is `benchmarks/extreme/REPORT.md`.
