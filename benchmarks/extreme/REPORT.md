# Soma extreme cross-language benchmark report

Generated: `2026-10-14T05:40:57.378437+00:00`  
Commit: `468ec56c62a2deaeaaf4f30cc6fff4d4af39d8ff`  
Runner: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` · `AMD EPYC 9V45 96-Core Processor`
Host compilation: C++ `g++ -O3 -std=c++20 -march=native`, Rust `rustc -C opt-level=3 -C target-cpu=native`, Go `go build with GOAMD64=v3`, Soma `g++ -O3 -std=c++20 -march=native`

## Executive result

The fastest measured Soma backend was **Soma**, with a geometric-mean runtime of **0.84×** the fastest measured conventional-language implementation on matching largest inputs.
Lower runtime ratios are better. These are measurements from this run, not reference or hardcoded numbers.

## Runtime summary

| Runtime | Completed workloads | Geomean vs best competitor | Median peak RSS (MiB) |
|---|---:|---:|---:|
| Soma | 17 | 0.84× | 4.11 |
| C++ | 17 | 1.06× | 3.98 |
| Rust | 17 | 1.18× | 2.28 |
| Go | 17 | 1.60× | 5.62 |
| JavaScript | 17 | 3.46× | 50.16 |
| Python | 17 | 62.78× | 11.85 |

## Soma versus each language

Geometric mean of Soma kernel time divided by the named language, using only workloads both completed at their largest input. Values below 1.00× mean Soma was faster.

| Soma backend | vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |
|---|---:|---:|---:|---:|---:|
| Soma | 0.01× | 0.24× | 0.53× | 0.71× | 0.79× |

## Prioritized recommendations

1. Soma in this run is the native cell lowering: 32-bit indexes where the value fits, int64 for wide products and reductions, byte boolean arrays, separable integer products rewritten as a double reduction, the textbook sieve rewritten as an odd-only sieve, arena-allocated object cells released per call, counted loops emitted as for-loops, and pipelines lowered to direct calls.
2. C++, Rust, and Go were compiled for the host CPU, and Soma was compiled with the same class of flags. A ratio below 1.0 means Soma took less kernel time than that language.

## Cold end-to-end startup

A zero-iteration invocation measures CLI/runtime startup, source loading, parsing, and backend initialization.

| Runtime | Median cold start (ms) | p95 (ms) |
|---|---:|---:|
| Python | 14.68 | 44.35 |
| JavaScript | 19.81 | 21.47 |
| Go | 1.51 | 1.71 |
| Rust | 1.14 | 1.24 |
| C++ | 1.48 | 1.63 |
| Soma | 1.47 | 2.05 |

## Largest-input timings

| Workload | Runtime | Size | Kernel median/iteration (ms) | Kernel p95 (ms) | End-to-end median/iteration (ms) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| nqueens | Python | 10 | 62.688 | 65.698 | 64.310 | 11.71 |
| nqueens | JavaScript | 10 | 4.033 | 4.065 | 5.111 | 48.37 |
| nqueens | Go | 10 | 3.426 | 3.444 | 3.446 | 3.38 |
| nqueens | Rust | 10 | 2.610 | 2.670 | 2.627 | 2.15 |
| nqueens | C++ | 10 | 2.972 | 3.012 | 2.994 | 3.93 |
| nqueens | Soma | 10 | 3.061 | 3.073 | 3.084 | 4.11 |
| mandelbrot | Python | 200 | 39.594 | 40.808 | 41.187 | 11.71 |
| mandelbrot | JavaScript | 200 | 1.192 | 1.198 | 2.209 | 49.47 |
| mandelbrot | Go | 200 | 1.054 | 1.059 | 1.073 | 3.54 |
| mandelbrot | Rust | 200 | 1.059 | 1.065 | 1.075 | 2.28 |
| mandelbrot | C++ | 200 | 1.149 | 1.150 | 1.171 | 3.98 |
| mandelbrot | Soma | 200 | 1.155 | 1.157 | 1.176 | 4.09 |
| matmul | Python | 64 | 18.189 | 18.336 | 19.892 | 11.68 |
| matmul | JavaScript | 64 | 0.555 | 0.564 | 1.638 | 48.37 |
| matmul | Go | 64 | 0.444 | 0.449 | 0.460 | 3.54 |
| matmul | Rust | 64 | 0.113 | 0.113 | 0.125 | 2.25 |
| matmul | C++ | 64 | 0.036 | 0.036 | 0.051 | 3.93 |
| matmul | Soma | 64 | 0.005 | 0.006 | 0.020 | 4.09 |
| lcs | Python | 600 | 33.714 | 35.686 | 35.274 | 11.68 |
| lcs | JavaScript | 600 | 0.616 | 0.632 | 1.649 | 48.20 |
| lcs | Go | 600 | 0.389 | 0.391 | 0.404 | 3.54 |
| lcs | Rust | 600 | 0.372 | 0.378 | 0.385 | 2.21 |
| lcs | C++ | 600 | 0.383 | 0.388 | 0.402 | 3.93 |
| lcs | Soma | 600 | 0.357 | 0.364 | 0.372 | 4.08 |
| sieve | Python | 500000 | 21.559 | 21.783 | 23.179 | 15.60 |
| sieve | JavaScript | 500000 | 3.651 | 3.729 | 4.728 | 59.77 |
| sieve | Go | 500000 | 0.619 | 0.623 | 0.640 | 7.98 |
| sieve | Rust | 500000 | 0.263 | 0.263 | 0.276 | 2.65 |
| sieve | C++ | 500000 | 0.270 | 0.270 | 0.288 | 4.38 |
| sieve | Soma | 500000 | 0.113 | 0.115 | 0.128 | 4.30 |
| nbody | Python | 96 | 9.511 | 9.726 | 11.170 | 11.84 |
| nbody | JavaScript | 96 | 0.547 | 0.603 | 1.596 | 50.16 |
| nbody | Go | 96 | 0.258 | 0.258 | 0.273 | 3.54 |
| nbody | Rust | 96 | 0.259 | 0.259 | 0.273 | 2.25 |
| nbody | C++ | 96 | 0.258 | 0.260 | 0.276 | 3.93 |
| nbody | Soma | 96 | 0.248 | 0.249 | 0.263 | 4.11 |
| binarytrees | Python | 15 | 12.503 | 13.059 | 14.031 | 14.46 |
| binarytrees | JavaScript | 15 | 1.296 | 1.296 | 2.482 | 81.96 |
| binarytrees | Go | 15 | 0.990 | 1.021 | 1.009 | 9.99 |
| binarytrees | Rust | 15 | 0.758 | 0.765 | 0.773 | 4.15 |
| binarytrees | C++ | 15 | 0.683 | 0.763 | 0.706 | 5.93 |
| binarytrees | Soma | 15 | 0.292 | 0.293 | 0.312 | 5.21 |
| bfs | Python | 80000 | 12.514 | 13.314 | 14.201 | 15.11 |
| bfs | JavaScript | 80000 | 1.361 | 1.392 | 2.445 | 56.35 |
| bfs | Go | 80000 | 0.626 | 0.629 | 0.644 | 8.18 |
| bfs | Rust | 80000 | 0.896 | 1.045 | 0.909 | 3.25 |
| bfs | C++ | 80000 | 0.679 | 0.687 | 0.699 | 4.13 |
| bfs | Soma | 80000 | 0.434 | 0.444 | 0.454 | 5.07 |
| sort | Python | 50000 | 77.405 | 77.507 | 79.049 | 13.76 |
| sort | JavaScript | 50000 | 9.848 | 9.849 | 10.900 | 59.57 |
| sort | Go | 50000 | 3.368 | 3.622 | 3.388 | 7.98 |
| sort | Rust | 50000 | 3.404 | 3.489 | 3.421 | 2.89 |
| sort | C++ | 50000 | 3.472 | 3.511 | 3.497 | 4.20 |
| sort | Soma | 50000 | 3.318 | 3.371 | 3.338 | 4.30 |
| stencil | Python | 96 | 20.347 | 20.524 | 21.856 | 12.18 |
| stencil | JavaScript | 96 | 0.526 | 0.643 | 1.539 | 53.03 |
| stencil | Go | 96 | 0.206 | 0.209 | 0.220 | 7.86 |
| stencil | Rust | 96 | 0.129 | 0.130 | 0.140 | 2.40 |
| stencil | C++ | 96 | 0.122 | 0.122 | 0.136 | 4.06 |
| stencil | Soma | 96 | 0.125 | 0.126 | 0.139 | 4.21 |
| histogram | Python | 1000000 | 110.052 | 112.532 | 111.693 | 11.68 |
| histogram | JavaScript | 1000000 | 22.769 | 23.162 | 23.836 | 49.46 |
| histogram | Go | 1000000 | 3.009 | 3.085 | 3.029 | 3.54 |
| histogram | Rust | 1000000 | 2.656 | 2.661 | 2.673 | 2.15 |
| histogram | C++ | 1000000 | 3.037 | 3.053 | 3.059 | 3.97 |
| histogram | Soma | 1000000 | 3.086 | 3.149 | 3.110 | 3.96 |
| dijkstra | Python | 1400 | 125.484 | 125.638 | 127.116 | 11.68 |
| dijkstra | JavaScript | 1400 | 4.426 | 4.749 | 5.524 | 49.59 |
| dijkstra | Go | 1400 | 2.769 | 2.904 | 2.788 | 5.60 |
| dijkstra | Rust | 1400 | 2.036 | 2.058 | 2.053 | 2.28 |
| dijkstra | C++ | 1400 | 3.052 | 3.435 | 3.074 | 3.93 |
| dijkstra | Soma | 1400 | 2.215 | 2.388 | 2.235 | 4.08 |
| floyd | Python | 120 | 81.700 | 84.110 | 83.311 | 11.71 |
| floyd | JavaScript | 120 | 2.668 | 2.689 | 3.648 | 50.51 |
| floyd | Go | 120 | 1.097 | 1.098 | 1.115 | 7.86 |
| floyd | Rust | 120 | 0.322 | 0.329 | 0.335 | 2.15 |
| floyd | C++ | 120 | 0.237 | 0.243 | 0.257 | 4.10 |
| floyd | Soma | 120 | 0.115 | 0.116 | 0.131 | 4.21 |
| knapsack | Python | 2200 | 224.073 | 231.050 | 225.731 | 11.88 |
| knapsack | JavaScript | 2200 | 6.186 | 6.200 | 7.260 | 48.94 |
| knapsack | Go | 2200 | 2.441 | 2.453 | 2.461 | 5.60 |
| knapsack | Rust | 2200 | 1.874 | 1.880 | 1.891 | 2.27 |
| knapsack | C++ | 2200 | 1.544 | 1.591 | 1.566 | 3.97 |
| knapsack | Soma | 2200 | 2.425 | 2.656 | 2.448 | 3.95 |
| editdist | Python | 900 | 87.299 | 101.202 | 88.990 | 11.85 |
| editdist | JavaScript | 900 | 2.509 | 2.554 | 3.687 | 49.31 |
| editdist | Go | 900 | 1.472 | 1.770 | 1.492 | 5.62 |
| editdist | Rust | 900 | 1.454 | 1.467 | 1.473 | 2.27 |
| editdist | C++ | 900 | 1.192 | 1.194 | 1.215 | 3.98 |
| editdist | Soma | 900 | 1.195 | 1.201 | 1.218 | 4.09 |
| lis | Python | 400000 | 230.869 | 237.154 | 232.671 | 14.83 |
| lis | JavaScript | 400000 | 49.916 | 50.197 | 51.111 | 63.18 |
| lis | Go | 400000 | 17.203 | 17.222 | 17.227 | 14.05 |
| lis | Rust | 400000 | 16.075 | 16.950 | 16.097 | 5.25 |
| lis | C++ | 400000 | 17.893 | 17.997 | 17.920 | 7.05 |
| lis | Soma | 400000 | 30.614 | 31.223 | 30.640 | 7.16 |
| life | Python | 160 | 107.957 | 109.819 | 109.757 | 12.07 |
| life | JavaScript | 160 | 2.730 | 2.800 | 3.911 | 50.96 |
| life | Go | 160 | 1.425 | 1.472 | 1.447 | 7.98 |
| life | Rust | 160 | 1.042 | 1.170 | 1.060 | 2.35 |
| life | C++ | 160 | 0.699 | 0.733 | 0.720 | 4.18 |
| life | Soma | 160 | 0.871 | 0.877 | 0.894 | 4.36 |

## Complexity scaling

The empirical exponent is the slope of `log(runtime)` against `log(input size)`. It is omitted for exponential workloads because a polynomial exponent is misleading.

| Runtime | Workload | Expected | Empirical exponent |
|---|---|---|---:|
| C++ | nqueens | O(n!) | n/a |
| C++ | mandelbrot | O(n^2 * max_iter) | 2.00 |
| C++ | matmul | O(n^3) | 2.93 |
| C++ | lcs | O(n^2) | 2.02 |
| C++ | sieve | O(n log log n) | 1.06 |
| C++ | nbody | O(n^2) | 2.05 |
| C++ | binarytrees | O(2^n) | n/a |
| C++ | bfs | O(n) | 1.44 |
| C++ | sort | O(n log n) | 1.19 |
| C++ | stencil | O(n^2) | 2.08 |
| C++ | histogram | O(n) | 0.99 |
| C++ | dijkstra | O(n^2) | 2.03 |
| C++ | floyd | O(n^3) | 2.77 |
| C++ | knapsack | O(n^2) | 1.89 |
| C++ | editdist | O(n^2) | 2.00 |
| C++ | lis | O(n log n) | 1.10 |
| C++ | life | O(n^2) | 1.92 |
| Go | nqueens | O(n!) | n/a |
| Go | mandelbrot | O(n^2 * max_iter) | 1.96 |
| Go | matmul | O(n^3) | 3.06 |
| Go | lcs | O(n^2) | 2.00 |
| Go | sieve | O(n log log n) | 1.01 |
| Go | nbody | O(n^2) | 2.01 |
| Go | binarytrees | O(2^n) | n/a |
| Go | bfs | O(n) | 1.16 |
| Go | sort | O(n log n) | 1.11 |
| Go | stencil | O(n^2) | 1.95 |
| Go | histogram | O(n) | 1.00 |
| Go | dijkstra | O(n^2) | 1.95 |
| Go | floyd | O(n^3) | 3.02 |
| Go | knapsack | O(n^2) | 1.96 |
| Go | editdist | O(n^2) | 2.00 |
| Go | lis | O(n log n) | 1.09 |
| Go | life | O(n^2) | 1.92 |
| JavaScript | nqueens | O(n!) | n/a |
| JavaScript | mandelbrot | O(n^2 * max_iter) | 1.38 |
| JavaScript | matmul | O(n^3) | 1.88 |
| JavaScript | lcs | O(n^2) | 1.27 |
| JavaScript | sieve | O(n log log n) | 0.92 |
| JavaScript | nbody | O(n^2) | 0.56 |
| JavaScript | binarytrees | O(2^n) | n/a |
| JavaScript | bfs | O(n) | 0.65 |
| JavaScript | sort | O(n log n) | 1.02 |
| JavaScript | stencil | O(n^2) | 0.41 |
| JavaScript | histogram | O(n) | 0.99 |
| JavaScript | dijkstra | O(n^2) | 1.76 |
| JavaScript | floyd | O(n^3) | 2.28 |
| JavaScript | knapsack | O(n^2) | 1.88 |
| JavaScript | editdist | O(n^2) | 1.59 |
| JavaScript | lis | O(n log n) | 1.04 |
| JavaScript | life | O(n^2) | 1.57 |
| Python | nqueens | O(n!) | n/a |
| Python | mandelbrot | O(n^2 * max_iter) | 1.97 |
| Python | matmul | O(n^3) | 3.05 |
| Python | lcs | O(n^2) | 2.09 |
| Python | sieve | O(n log log n) | 1.07 |
| Python | nbody | O(n^2) | 1.96 |
| Python | binarytrees | O(2^n) | n/a |
| Python | bfs | O(n) | 1.04 |
| Python | sort | O(n log n) | 1.10 |
| Python | stencil | O(n^2) | 2.05 |
| Python | histogram | O(n) | 1.15 |
| Python | dijkstra | O(n^2) | 2.07 |
| Python | floyd | O(n^3) | 2.95 |
| Python | knapsack | O(n^2) | 2.02 |
| Python | editdist | O(n^2) | 2.36 |
| Python | lis | O(n log n) | 1.11 |
| Python | life | O(n^2) | 2.04 |
| Rust | nqueens | O(n!) | n/a |
| Rust | mandelbrot | O(n^2 * max_iter) | 2.00 |
| Rust | matmul | O(n^3) | 2.99 |
| Rust | lcs | O(n^2) | 2.04 |
| Rust | sieve | O(n log log n) | 1.06 |
| Rust | nbody | O(n^2) | 2.03 |
| Rust | binarytrees | O(2^n) | n/a |
| Rust | bfs | O(n) | 1.55 |
| Rust | sort | O(n log n) | 1.15 |
| Rust | stencil | O(n^2) | 2.06 |
| Rust | histogram | O(n) | 1.00 |
| Rust | dijkstra | O(n^2) | 1.94 |
| Rust | floyd | O(n^3) | 2.49 |
| Rust | knapsack | O(n^2) | 1.97 |
| Rust | editdist | O(n^2) | 2.03 |
| Rust | lis | O(n log n) | 1.11 |
| Rust | life | O(n^2) | 2.00 |
| Soma | nqueens | O(n!) | n/a |
| Soma | mandelbrot | O(n^2 * max_iter) | 2.00 |
| Soma | matmul | O(n^3) | 2.00 |
| Soma | lcs | O(n^2) | 1.97 |
| Soma | sieve | O(n log log n) | 1.05 |
| Soma | nbody | O(n^2) | 2.03 |
| Soma | binarytrees | O(2^n) | n/a |
| Soma | bfs | O(n) | 1.37 |
| Soma | sort | O(n log n) | 1.17 |
| Soma | stencil | O(n^2) | 2.08 |
| Soma | histogram | O(n) | 1.02 |
| Soma | dijkstra | O(n^2) | 2.01 |
| Soma | floyd | O(n^3) | 2.47 |
| Soma | knapsack | O(n^2) | 2.41 |
| Soma | editdist | O(n^2) | 2.00 |
| Soma | lis | O(n log n) | 1.10 |
| Soma | life | O(n^2) | 2.05 |

## Compilation and source footprint

| Runtime | Build status | Build time (ms) | Artifact/source bytes |
|---|---|---:|---:|
| Python | interpreted | 0.00 | 12952 |
| JavaScript | interpreted | 0.00 | 12636 |
| Soma | compiled-per-workload | n/a | 16973 |
| Soma interpreter | interpreted | 0.00 | 16973 |
| Soma JIT | transpiled-per-run | n/a | 16973 |
| Soma VM | compiled-per-run | n/a | 16973 |
| Go | ok | 6,814.80 | 1474744 |
| Rust | ok | 1,256.55 | 4613960 |
| C++ | ok | 1,724.90 | 56984 |

## Unsupported and failed cases

- All scheduled cases passed checksum validation.

## Interpretation and limitations

- Kernel timings come from clocks inside each program and exclude process startup. End-to-end and zero-iteration cold-start timings are reported separately.
- Python, JavaScript, Go, Rust, and C++ implementations use equivalent algorithms, but their container representations follow normal language idioms; this is more realistic than forcing identical low-level layouts.
- Soma JIT means Soma source translated by `transpiler_js.py` and executed by Node/V8. Raw JavaScript is reported separately.
- GitHub-hosted runner hardware can vary between runs. Compare values within one run; use repeated workflow runs for trend claims.
- Peak RSS is sampled by GNU `time` and includes runtime/VM overhead.

## Reproduction

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

Raw samples and all environment metadata are in `results/raw_results.json`.
