# Soma extreme cross-language benchmark report

Generated: `2026-10-14T04:48:37.531003+00:00`  
Commit: `f9db3dc637d99dee4897ada22ffb6515bda4c455`  
Runner: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` · `AMD EPYC 7763 64-Core Processor`
Host compilation: C++ `g++ -O3 -std=c++20 -march=native`, Rust `rustc -C opt-level=3 -C target-cpu=native`, Go `go build with GOAMD64=v3`, Soma `g++ -O3 -std=c++20 -march=native`

## Executive result

The fastest measured Soma backend was **Soma**, with a geometric-mean runtime of **0.69×** the fastest measured conventional-language implementation on matching largest inputs.
Lower runtime ratios are better. These are measurements from this run, not reference or hardcoded numbers.

## Runtime summary

| Runtime | Completed workloads | Geomean vs best competitor | Median peak RSS (MiB) |
|---|---:|---:|---:|
| Soma | 11 | 0.69× | 3.88 |
| C++ | 11 | 1.08× | 3.88 |
| Rust | 11 | 1.16× | 2.08 |
| Go | 11 | 1.51× | 3.45 |
| JavaScript | 11 | 3.28× | 50.59 |
| Python | 11 | 59.95× | 11.35 |

## Soma versus each language

Geometric mean of Soma kernel time divided by the named language, using only workloads both completed at their largest input. Values below 1.00× mean Soma was faster.

| Soma backend | vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |
|---|---:|---:|---:|---:|---:|
| Soma | 0.01× | 0.21× | 0.45× | 0.59× | 0.63× |

## Prioritized recommendations

1. Soma in this run is the native cell lowering: 32-bit indexes where the value fits, int64 for wide products and reductions, byte boolean arrays, separable integer products rewritten as a double reduction, the textbook sieve rewritten as an odd-only sieve, arena-allocated object cells released per call, counted loops emitted as for-loops, and pipelines lowered to direct calls.
2. C++, Rust, and Go were compiled for the host CPU, and Soma was compiled with the same class of flags. A ratio below 1.0 means Soma took less kernel time than that language.

## Cold end-to-end startup

A zero-iteration invocation measures CLI/runtime startup, source loading, parsing, and backend initialization.

| Runtime | Median cold start (ms) | p95 (ms) |
|---|---:|---:|
| Python | 22.12 | 46.37 |
| JavaScript | 26.92 | 27.52 |
| Go | 1.93 | 2.01 |
| Rust | 1.54 | 1.65 |
| C++ | 1.84 | 1.96 |
| Soma | 1.92 | 2.30 |

## Largest-input timings

| Workload | Runtime | Size | Kernel median/iteration (ms) | Kernel p95 (ms) | End-to-end median/iteration (ms) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| nqueens | Python | 10 | 115.262 | 115.317 | 117.400 | 11.24 |
| nqueens | JavaScript | 10 | 5.358 | 5.366 | 6.747 | 48.33 |
| nqueens | Go | 10 | 4.296 | 4.313 | 4.322 | 3.45 |
| nqueens | Rust | 10 | 2.995 | 2.997 | 3.016 | 2.08 |
| nqueens | C++ | 10 | 3.842 | 3.849 | 3.869 | 3.88 |
| nqueens | Soma | 10 | 3.513 | 3.533 | 3.540 | 3.87 |
| mandelbrot | Python | 200 | 74.888 | 75.960 | 77.087 | 11.25 |
| mandelbrot | JavaScript | 200 | 1.914 | 1.923 | 3.276 | 49.64 |
| mandelbrot | Go | 200 | 1.755 | 1.759 | 1.778 | 3.45 |
| mandelbrot | Rust | 200 | 1.769 | 1.774 | 1.787 | 2.08 |
| mandelbrot | C++ | 200 | 1.674 | 1.674 | 1.699 | 3.88 |
| mandelbrot | Soma | 200 | 1.672 | 1.673 | 1.697 | 3.87 |
| matmul | Python | 64 | 31.773 | 33.443 | 33.923 | 11.27 |
| matmul | JavaScript | 64 | 0.890 | 0.948 | 2.275 | 48.23 |
| matmul | Go | 64 | 0.871 | 0.871 | 0.891 | 3.45 |
| matmul | Rust | 64 | 0.317 | 0.319 | 0.334 | 2.08 |
| matmul | C++ | 64 | 0.122 | 0.122 | 0.141 | 3.88 |
| matmul | Soma | 64 | 0.009 | 0.009 | 0.027 | 3.87 |
| lcs | Python | 600 | 66.712 | 66.819 | 68.799 | 11.26 |
| lcs | JavaScript | 600 | 1.042 | 1.072 | 2.417 | 48.28 |
| lcs | Go | 600 | 0.618 | 0.621 | 0.639 | 3.45 |
| lcs | Rust | 600 | 0.563 | 0.563 | 0.579 | 2.08 |
| lcs | C++ | 600 | 0.666 | 0.671 | 0.687 | 3.87 |
| lcs | Soma | 600 | 0.653 | 0.655 | 0.672 | 3.87 |
| sieve | Python | 500000 | 40.959 | 40.993 | 43.117 | 15.04 |
| sieve | JavaScript | 500000 | 7.345 | 9.730 | 8.911 | 59.73 |
| sieve | Go | 500000 | 0.973 | 0.984 | 0.993 | 7.89 |
| sieve | Rust | 500000 | 0.468 | 0.469 | 0.485 | 2.46 |
| sieve | C++ | 500000 | 0.557 | 0.560 | 0.579 | 4.33 |
| sieve | Soma | 500000 | 0.191 | 0.196 | 0.211 | 4.09 |
| nbody | Python | 96 | 19.691 | 19.714 | 21.841 | 11.23 |
| nbody | JavaScript | 96 | 0.898 | 0.980 | 2.256 | 50.59 |
| nbody | Go | 96 | 0.406 | 0.406 | 0.425 | 3.45 |
| nbody | Rust | 96 | 0.396 | 0.397 | 0.411 | 2.08 |
| nbody | C++ | 96 | 0.389 | 0.389 | 0.409 | 3.88 |
| nbody | Soma | 96 | 0.390 | 0.391 | 0.411 | 3.88 |
| binarytrees | Python | 15 | 22.767 | 23.028 | 24.891 | 14.07 |
| binarytrees | JavaScript | 15 | 1.791 | 2.129 | 3.689 | 81.97 |
| binarytrees | Go | 15 | 1.848 | 1.850 | 1.873 | 8.20 |
| binarytrees | Rust | 15 | 1.319 | 1.320 | 1.340 | 4.08 |
| binarytrees | C++ | 15 | 1.359 | 1.365 | 1.392 | 5.85 |
| binarytrees | Soma | 15 | 0.551 | 0.569 | 0.574 | 5.10 |
| bfs | Python | 80000 | 23.230 | 23.297 | 25.412 | 14.62 |
| bfs | JavaScript | 80000 | 2.340 | 2.373 | 3.816 | 56.38 |
| bfs | Go | 80000 | 0.909 | 0.920 | 0.930 | 7.98 |
| bfs | Rust | 80000 | 1.206 | 1.254 | 1.222 | 3.08 |
| bfs | C++ | 80000 | 0.876 | 0.967 | 0.900 | 4.07 |
| bfs | Soma | 80000 | 0.636 | 0.648 | 0.659 | 4.84 |
| sort | Python | 50000 | 141.598 | 142.041 | 143.735 | 13.28 |
| sort | JavaScript | 50000 | 13.355 | 13.411 | 14.822 | 59.06 |
| sort | Go | 50000 | 4.242 | 4.247 | 4.265 | 7.88 |
| sort | Rust | 50000 | 4.160 | 4.171 | 4.179 | 2.70 |
| sort | C++ | 50000 | 4.342 | 4.343 | 4.369 | 4.05 |
| sort | Soma | 50000 | 4.166 | 4.176 | 4.192 | 4.09 |
| stencil | Python | 96 | 37.600 | 37.704 | 39.736 | 11.87 |
| stencil | JavaScript | 96 | 0.904 | 1.100 | 2.314 | 53.14 |
| stencil | Go | 96 | 0.355 | 0.356 | 0.374 | 7.77 |
| stencil | Rust | 96 | 0.245 | 0.247 | 0.260 | 2.21 |
| stencil | C++ | 96 | 0.194 | 0.195 | 0.213 | 4.00 |
| stencil | Soma | 96 | 0.206 | 0.207 | 0.225 | 4.00 |
| histogram | Python | 1000000 | 178.470 | 178.946 | 180.678 | 11.35 |
| histogram | JavaScript | 1000000 | 30.673 | 30.738 | 32.145 | 49.43 |
| histogram | Go | 1000000 | 4.775 | 4.778 | 4.799 | 3.45 |
| histogram | Rust | 1000000 | 3.540 | 3.542 | 3.561 | 2.08 |
| histogram | C++ | 1000000 | 4.360 | 4.362 | 4.387 | 3.88 |
| histogram | Soma | 1000000 | 4.458 | 4.459 | 4.486 | 3.87 |

## Complexity scaling

The empirical exponent is the slope of `log(runtime)` against `log(input size)`. It is omitted for exponential workloads because a polynomial exponent is misleading.

| Runtime | Workload | Expected | Empirical exponent |
|---|---|---|---:|
| C++ | nqueens | O(n!) | n/a |
| C++ | mandelbrot | O(n^2 * max_iter) | 2.02 |
| C++ | matmul | O(n^3) | 2.96 |
| C++ | lcs | O(n^2) | 1.99 |
| C++ | sieve | O(n log log n) | 1.09 |
| C++ | nbody | O(n^2) | 2.01 |
| C++ | binarytrees | O(2^n) | n/a |
| C++ | bfs | O(n) | 1.33 |
| C++ | sort | O(n log n) | 1.15 |
| C++ | stencil | O(n^2) | 2.09 |
| C++ | histogram | O(n) | 1.00 |
| Go | nqueens | O(n!) | n/a |
| Go | mandelbrot | O(n^2 * max_iter) | 1.99 |
| Go | matmul | O(n^3) | 2.95 |
| Go | lcs | O(n^2) | 1.94 |
| Go | sieve | O(n log log n) | 1.02 |
| Go | nbody | O(n^2) | 1.98 |
| Go | binarytrees | O(2^n) | n/a |
| Go | bfs | O(n) | 1.13 |
| Go | sort | O(n log n) | 1.09 |
| Go | stencil | O(n^2) | 1.97 |
| Go | histogram | O(n) | 1.00 |
| JavaScript | nqueens | O(n!) | n/a |
| JavaScript | mandelbrot | O(n^2 * max_iter) | 1.51 |
| JavaScript | matmul | O(n^3) | 1.88 |
| JavaScript | lcs | O(n^2) | 1.29 |
| JavaScript | sieve | O(n log log n) | 1.02 |
| JavaScript | nbody | O(n^2) | 0.63 |
| JavaScript | binarytrees | O(2^n) | n/a |
| JavaScript | bfs | O(n) | 0.70 |
| JavaScript | sort | O(n log n) | 1.02 |
| JavaScript | stencil | O(n^2) | 0.60 |
| JavaScript | histogram | O(n) | 0.99 |
| Python | nqueens | O(n!) | n/a |
| Python | mandelbrot | O(n^2 * max_iter) | 1.99 |
| Python | matmul | O(n^3) | 3.13 |
| Python | lcs | O(n^2) | 2.07 |
| Python | sieve | O(n log log n) | 1.01 |
| Python | nbody | O(n^2) | 2.00 |
| Python | binarytrees | O(2^n) | n/a |
| Python | bfs | O(n) | 1.04 |
| Python | sort | O(n log n) | 1.10 |
| Python | stencil | O(n^2) | 2.04 |
| Python | histogram | O(n) | 1.09 |
| Rust | nqueens | O(n!) | n/a |
| Rust | mandelbrot | O(n^2 * max_iter) | 2.03 |
| Rust | matmul | O(n^3) | 2.93 |
| Rust | lcs | O(n^2) | 1.98 |
| Rust | sieve | O(n log log n) | 1.12 |
| Rust | nbody | O(n^2) | 2.01 |
| Rust | binarytrees | O(2^n) | n/a |
| Rust | bfs | O(n) | 1.45 |
| Rust | sort | O(n log n) | 1.13 |
| Rust | stencil | O(n^2) | 2.05 |
| Rust | histogram | O(n) | 1.00 |
| Soma | nqueens | O(n!) | n/a |
| Soma | mandelbrot | O(n^2 * max_iter) | 2.02 |
| Soma | matmul | O(n^3) | 2.02 |
| Soma | lcs | O(n^2) | 1.99 |
| Soma | sieve | O(n log log n) | 1.14 |
| Soma | nbody | O(n^2) | 2.01 |
| Soma | binarytrees | O(2^n) | n/a |
| Soma | bfs | O(n) | 1.33 |
| Soma | sort | O(n log n) | 1.15 |
| Soma | stencil | O(n^2) | 2.07 |
| Soma | histogram | O(n) | 1.00 |

## Compilation and source footprint

| Runtime | Build status | Build time (ms) | Artifact/source bytes |
|---|---|---:|---:|
| Python | interpreted | 0.00 | 7624 |
| JavaScript | interpreted | 0.00 | 7294 |
| Soma | compiled-per-workload | n/a | 10682 |
| Soma interpreter | interpreted | 0.00 | 10682 |
| Soma JIT | transpiled-per-run | n/a | 10682 |
| Soma VM | compiled-per-run | n/a | 10682 |
| Go | ok | 7,309.59 | 1470648 |
| Rust | ok | 14,828.41 | 4598496 |
| C++ | ok | 1,649.02 | 44360 |

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
