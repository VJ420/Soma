# Soma extreme cross-language benchmark report

Generated: `2026-10-14T02:38:00.598597+00:00`  
Commit: `53abf5ba45c2a23de5e5d6ab1feacef432355571`  
Runner: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` · `AMD EPYC 9V45 96-Core Processor`

## Executive result

The fastest measured Soma backend was **Soma JIT**, with a geometric-mean runtime of **9.58×** the fastest measured conventional-language implementation on matching largest inputs.
Lower runtime ratios are better. These are measurements from this run, not reference or hardcoded numbers.

## Runtime summary

| Runtime | Completed workloads | Geomean vs best competitor | Median peak RSS (MiB) |
|---|---:|---:|---:|
| C++ | 7 | 1.04× | 3.96 |
| Rust | 7 | 1.06× | 2.22 |
| Go | 7 | 1.41× | 3.47 |
| JavaScript | 7 | 5.21× | 49.54 |
| Soma JIT | 7 | 9.58× | 49.77 |
| Python | 7 | 40.80× | 11.10 |
| Soma VM | 2 | 5,578.72× | 16.68 |
| Soma interpreter | 7 | 6,231.68× | 16.68 |

## Soma versus each language

Geometric mean of Soma kernel time divided by the named language, using only workloads both completed at their largest input. Values below 1.00× mean Soma was faster.

| Soma backend | vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |
|---|---:|---:|---:|---:|---:|
| Soma JIT | 0.23× | 1.84× | 6.78× | 9.02× | 9.23× |
| Soma VM | 129.06× | 2,181.36× | 4,799.37× | 5,367.32× | 5,379.03× |
| Soma interpreter | 152.75× | 1,197.09× | 4,408.17× | 5,867.01× | 6,003.85× |

## Prioritized recommendations

1. Ship index get/set in `compiler.py` / `vm.py`. That single gap blocked N-Queens, LCS, sieve, and N-body on the VM path in this run.
2. Replace AST walking in the default interpreter with bytecode execution for `soma_cli.py run`. On matching largest inputs the interpreter was 153× slower than CPython.
3. Make the JS transpiler emit packed numeric loops (typed arrays, fewer object allocations) so Soma JIT can close the remaining gap to handwritten JavaScript.
4. Implement nested callable cells on VM instances so allocation/recursion workloads like binary trees are not unsupported.
5. Expose a high-resolution clock builtin. Soma kernels currently time with `time()`, which quantizes sub-millisecond JIT loops and flattens empirical exponents.
6. Cut CLI/transpile startup. Zero-iteration Soma JIT and interpreter launches were tens of milliseconds; compiled Go/Rust/C++ binaries were about 1–2 ms.

## Cold end-to-end startup

A zero-iteration invocation measures CLI/runtime startup, source loading, parsing, and backend initialization.

| Runtime | Median cold start (ms) | p95 (ms) |
|---|---:|---:|
| Python | 14.55 | 21.78 |
| JavaScript | 21.77 | 113.60 |
| Go | 1.51 | 1.80 |
| Rust | 1.27 | 1.40 |
| C++ | 1.70 | 1.75 |
| Soma interpreter | 51.47 | 58.69 |
| Soma JIT | 74.60 | 76.08 |
| Soma VM | 53.64 | 54.03 |

## Largest-input timings

| Workload | Runtime | Size | Kernel median/iteration (ms) | Kernel p95 (ms) | End-to-end median/iteration (ms) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| nqueens | Python | 9 | 11.703 | 11.703 | 13.105 | 10.93 |
| nqueens | JavaScript | 9 | 0.963 | 0.972 | 2.057 | 48.45 |
| nqueens | Go | 9 | 0.809 | 0.813 | 0.828 | 3.47 |
| nqueens | Rust | 9 | 0.545 | 0.586 | 0.563 | 2.13 |
| nqueens | C++ | 9 | 0.600 | 0.608 | 0.622 | 3.92 |
| nqueens | Soma interpreter | 9 | 5,844.383 | 6,108.013 | 5,900.311 | 16.71 |
| nqueens | Soma JIT | 9 | 1.100 | 1.100 | 8.374 | 48.18 |
| mandelbrot | Python | 100 | 10.356 | 11.413 | 12.049 | 11.10 |
| mandelbrot | JavaScript | 100 | 0.434 | 0.448 | 1.595 | 49.73 |
| mandelbrot | Go | 100 | 0.276 | 0.277 | 0.295 | 3.47 |
| mandelbrot | Rust | 100 | 0.289 | 0.290 | 0.305 | 2.22 |
| mandelbrot | C++ | 100 | 0.267 | 0.272 | 0.289 | 3.96 |
| mandelbrot | Soma interpreter | 100 | 1,497.197 | 1,508.296 | 1,554.788 | 16.68 |
| mandelbrot | Soma JIT | 100 | 0.600 | 0.600 | 8.189 | 49.77 |
| mandelbrot | Soma VM | 100 | 1,511.657 | 1,530.227 | 1,564.186 | 16.68 |
| matmul | Python | 32 | 2.031 | 2.032 | 3.511 | 11.10 |
| matmul | JavaScript | 32 | 0.170 | 0.172 | 1.229 | 48.08 |
| matmul | Go | 32 | 0.055 | 0.055 | 0.070 | 3.47 |
| matmul | Rust | 32 | 0.042 | 0.042 | 0.055 | 2.25 |
| matmul | C++ | 32 | 0.045 | 0.046 | 0.063 | 3.96 |
| matmul | Soma interpreter | 32 | 242.770 | 249.036 | 296.825 | 16.67 |
| matmul | Soma JIT | 32 | 0.300 | 0.300 | 7.778 | 48.11 |
| matmul | Soma VM | 32 | 231.752 | 235.583 | 286.419 | 16.67 |
| lcs | Python | 240 | 4.636 | 4.652 | 6.075 | 11.13 |
| lcs | JavaScript | 240 | 0.214 | 0.222 | 1.281 | 48.35 |
| lcs | Go | 240 | 0.069 | 0.072 | 0.083 | 3.47 |
| lcs | Rust | 240 | 0.056 | 0.063 | 0.069 | 2.26 |
| lcs | C++ | 240 | 0.043 | 0.043 | 0.060 | 3.97 |
| lcs | Soma interpreter | 240 | 476.924 | 500.778 | 530.958 | 16.56 |
| lcs | Soma JIT | 240 | 0.300 | 0.400 | 7.795 | 48.59 |
| sieve | Python | 12000 | 0.427 | 0.443 | 1.918 | 11.11 |
| sieve | JavaScript | 12000 | 0.281 | 0.291 | 1.367 | 50.50 |
| sieve | Go | 12000 | 0.014 | 0.015 | 0.029 | 5.54 |
| sieve | Rust | 12000 | 0.007 | 0.007 | 0.018 | 2.13 |
| sieve | C++ | 12000 | 0.006 | 0.006 | 0.021 | 3.95 |
| sieve | Soma interpreter | 12000 | 108.877 | 110.382 | 163.627 | 17.06 |
| sieve | Soma JIT | 12000 | 0.600 | 0.600 | 8.115 | 49.95 |
| nbody | Python | 28 | 0.858 | 0.873 | 2.278 | 11.10 |
| nbody | JavaScript | 28 | 0.282 | 0.296 | 1.379 | 50.55 |
| nbody | Go | 28 | 0.022 | 0.023 | 0.037 | 3.47 |
| nbody | Rust | 28 | 0.022 | 0.022 | 0.034 | 2.13 |
| nbody | C++ | 28 | 0.022 | 0.022 | 0.037 | 3.95 |
| nbody | Soma interpreter | 28 | 123.653 | 125.045 | 177.915 | 16.56 |
| nbody | Soma JIT | 28 | 0.700 | 0.700 | 8.533 | 50.42 |
| binarytrees | Python | 11 | 0.606 | 0.609 | 1.834 | 11.26 |
| binarytrees | JavaScript | 11 | 0.116 | 0.117 | 1.017 | 49.54 |
| binarytrees | Go | 11 | 0.057 | 0.060 | 0.070 | 7.73 |
| binarytrees | Rust | 11 | 0.038 | 0.039 | 0.049 | 2.27 |
| binarytrees | C++ | 11 | 0.042 | 0.048 | 0.056 | 4.10 |
| binarytrees | Soma interpreter | 11 | 36.046 | 36.587 | 88.794 | 18.16 |
| binarytrees | Soma JIT | 11 | 0.400 | 0.400 | 7.614 | 51.70 |

## Complexity scaling

The empirical exponent is the slope of `log(runtime)` against `log(input size)`. It is omitted for exponential workloads because a polynomial exponent is misleading.

| Runtime | Workload | Expected | Empirical exponent |
|---|---|---|---:|
| C++ | nqueens | O(n!) | n/a |
| C++ | mandelbrot | O(n^2 * max_iter) | 1.96 |
| C++ | matmul | O(n^3) | 2.98 |
| C++ | lcs | O(n^2) | 2.01 |
| C++ | sieve | O(n log log n) | 1.02 |
| C++ | nbody | O(n^2) | 2.09 |
| C++ | binarytrees | O(2^n) | n/a |
| Go | nqueens | O(n!) | n/a |
| Go | mandelbrot | O(n^2 * max_iter) | 1.99 |
| Go | matmul | O(n^3) | 2.96 |
| Go | lcs | O(n^2) | 1.82 |
| Go | sieve | O(n log log n) | 0.97 |
| Go | nbody | O(n^2) | 2.08 |
| Go | binarytrees | O(2^n) | n/a |
| JavaScript | nqueens | O(n!) | n/a |
| JavaScript | mandelbrot | O(n^2 * max_iter) | 0.80 |
| JavaScript | matmul | O(n^3) | 0.86 |
| JavaScript | lcs | O(n^2) | 0.51 |
| JavaScript | sieve | O(n log log n) | 0.55 |
| JavaScript | nbody | O(n^2) | 0.57 |
| JavaScript | binarytrees | O(2^n) | n/a |
| Python | nqueens | O(n!) | n/a |
| Python | mandelbrot | O(n^2 * max_iter) | 1.98 |
| Python | matmul | O(n^3) | 3.04 |
| Python | lcs | O(n^2) | 1.99 |
| Python | sieve | O(n log log n) | 1.02 |
| Python | nbody | O(n^2) | 1.97 |
| Python | binarytrees | O(2^n) | n/a |
| Rust | nqueens | O(n!) | n/a |
| Rust | mandelbrot | O(n^2 * max_iter) | 1.97 |
| Rust | matmul | O(n^3) | 2.95 |
| Rust | lcs | O(n^2) | 1.90 |
| Rust | sieve | O(n log log n) | 0.99 |
| Rust | nbody | O(n^2) | 2.06 |
| Rust | binarytrees | O(2^n) | n/a |
| Soma JIT | nqueens | O(n!) | n/a |
| Soma JIT | mandelbrot | O(n^2 * max_iter) | 0.73 |
| Soma JIT | matmul | O(n^3) | 1.59 |
| Soma JIT | lcs | O(n^2) | 0.39 |
| Soma JIT | sieve | O(n log log n) | 0.61 |
| Soma JIT | nbody | O(n^2) | 1.47 |
| Soma JIT | binarytrees | O(2^n) | n/a |
| Soma VM | nqueens | O(n!) | n/a |
| Soma VM | mandelbrot | O(n^2 * max_iter) | 1.96 |
| Soma VM | matmul | O(n^3) | 2.96 |
| Soma VM | lcs | O(n^2) | n/a |
| Soma VM | sieve | O(n log log n) | n/a |
| Soma VM | nbody | O(n^2) | n/a |
| Soma VM | binarytrees | O(2^n) | n/a |
| Soma interpreter | nqueens | O(n!) | n/a |
| Soma interpreter | mandelbrot | O(n^2 * max_iter) | 1.96 |
| Soma interpreter | matmul | O(n^3) | 2.92 |
| Soma interpreter | lcs | O(n^2) | 1.99 |
| Soma interpreter | sieve | O(n log log n) | 1.00 |
| Soma interpreter | nbody | O(n^2) | 2.06 |
| Soma interpreter | binarytrees | O(2^n) | n/a |

## Compilation and source footprint

| Runtime | Build status | Build time (ms) | Artifact/source bytes |
|---|---|---:|---:|
| Python | interpreted | 0.00 | 4371 |
| JavaScript | interpreted | 0.00 | 4158 |
| Soma interpreter | interpreted | 0.00 | 6583 |
| Soma JIT | transpiled-per-run | n/a | 6583 |
| Soma VM | compiled-per-run | n/a | 6583 |
| Go | ok | 6,106.24 | 1470648 |
| Rust | ok | 867.09 | 4585808 |
| C++ | ok | 1,249.90 | 39984 |

## Unsupported and failed cases

- **Soma VM / nqueens / size 7**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / nqueens / size 8**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / nqueens / size 9**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / lcs / size 80**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / lcs / size 160**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / lcs / size 240**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / sieve / size 2000**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / sieve / size 6000**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / sieve / size 12000**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / nbody / size 12**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / nbody / size 20**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / nbody / size 28**: unsupported — The bytecode compiler does not implement index access or index assignment.
- **Soma VM / binarytrees / size 7**: unsupported — Nested callable cells are not callable through the current VM object representation.
- **Soma VM / binarytrees / size 9**: unsupported — Nested callable cells are not callable through the current VM object representation.
- **Soma VM / binarytrees / size 11**: unsupported — Nested callable cells are not callable through the current VM object representation.

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
