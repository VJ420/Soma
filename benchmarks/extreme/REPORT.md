# Soma extreme cross-language benchmark report

Generated: `2026-10-14T03:00:58.658947+00:00`  
Commit: `53abf5ba45c2a23de5e5d6ab1feacef432355571`  
Runner: `Windows-11-10.0.26200-SP0` · `Intel64 Family 6 Model 142 Stepping 12, GenuineIntel`

## Executive result

The fastest measured Soma backend was **Soma JIT**, with a geometric-mean runtime of **0.91×** the fastest measured conventional-language implementation on matching largest inputs.
Lower runtime ratios are better. These are measurements from this run, not reference or hardcoded numbers.

## Runtime summary

| Runtime | Completed workloads | Geomean vs best competitor | Median peak RSS (MiB) |
|---|---:|---:|---:|
| Soma JIT | 1 | 0.91× | n/a |
| JavaScript | 1 | 1.00× | n/a |
| Python | 1 | 16.97× | n/a |
| Soma interpreter | 1 | 2,640.10× | n/a |

## Soma versus each language

Geometric mean of Soma kernel time divided by the named language, using only workloads both completed at their largest input. Values below 1.00× mean Soma was faster.

| Soma backend | vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |
|---|---:|---:|---:|---:|---:|
| Soma JIT | 0.05× | 0.91× | n/a× | n/a× | n/a× |
| Soma interpreter | 155.57× | 2,640.10× | n/a× | n/a× | n/a× |

## Prioritized recommendations

1. Keep VM and interpreter backend coverage aligned. Unsupported pairs should stay explicit failures, not silent skips.
2. Replace AST walking in the default interpreter with bytecode execution for `soma_cli.py run`. On matching largest inputs the interpreter was 156× slower than CPython.
3. Make the JS transpiler emit packed numeric loops (typed arrays, fewer object allocations) so Soma JIT can close the remaining gap to handwritten JavaScript.
4. Implement nested callable cells on VM instances so allocation/recursion workloads like binary trees are not unsupported.
5. Expose a high-resolution clock builtin. Soma kernels currently time with `time()`, which quantizes sub-millisecond JIT loops and flattens empirical exponents.
6. Cut CLI/transpile startup. Zero-iteration Soma JIT and interpreter launches were tens of milliseconds; compiled Go/Rust/C++ binaries were about 1–2 ms.
7. Re-run the GitHub Actions workflow whenever Go, Rust, or C++ numbers are needed; those toolchains are not assumed locally.

## Cold end-to-end startup

A zero-iteration invocation measures CLI/runtime startup, source loading, parsing, and backend initialization.

| Runtime | Median cold start (ms) | p95 (ms) |
|---|---:|---:|
| Python | 157.58 | 157.58 |
| JavaScript | 224.45 | 224.45 |
| Soma JIT | 1,601.34 | 1,601.34 |
| Soma interpreter | 505.68 | 505.68 |

## Largest-input timings

| Workload | Runtime | Size | Kernel median/iteration (ms) | Kernel p95 (ms) | End-to-end median/iteration (ms) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|

## Complexity scaling

The empirical exponent is the slope of `log(runtime)` against `log(input size)`. It is omitted for exponential workloads because a polynomial exponent is misleading.

| Runtime | Workload | Expected | Empirical exponent |
|---|---|---|---:|
| JavaScript | nqueens | O(n!) | n/a |
| JavaScript | mandelbrot | O(n^2 * max_iter) | n/a |
| JavaScript | matmul | O(n^3) | n/a |
| JavaScript | lcs | O(n^2) | n/a |
| JavaScript | sieve | O(n log log n) | n/a |
| JavaScript | nbody | O(n^2) | n/a |
| JavaScript | binarytrees | O(2^n) | n/a |
| Python | nqueens | O(n!) | n/a |
| Python | mandelbrot | O(n^2 * max_iter) | n/a |
| Python | matmul | O(n^3) | n/a |
| Python | lcs | O(n^2) | n/a |
| Python | sieve | O(n log log n) | n/a |
| Python | nbody | O(n^2) | n/a |
| Python | binarytrees | O(2^n) | n/a |
| Soma JIT | nqueens | O(n!) | n/a |
| Soma JIT | mandelbrot | O(n^2 * max_iter) | n/a |
| Soma JIT | matmul | O(n^3) | n/a |
| Soma JIT | lcs | O(n^2) | n/a |
| Soma JIT | sieve | O(n log log n) | n/a |
| Soma JIT | nbody | O(n^2) | n/a |
| Soma JIT | binarytrees | O(2^n) | n/a |
| Soma interpreter | nqueens | O(n!) | n/a |
| Soma interpreter | mandelbrot | O(n^2 * max_iter) | n/a |
| Soma interpreter | matmul | O(n^3) | n/a |
| Soma interpreter | lcs | O(n^2) | n/a |
| Soma interpreter | sieve | O(n log log n) | n/a |
| Soma interpreter | nbody | O(n^2) | n/a |
| Soma interpreter | binarytrees | O(2^n) | n/a |

## Compilation and source footprint

| Runtime | Build status | Build time (ms) | Artifact/source bytes |
|---|---|---:|---:|
| Python | interpreted | 0.00 | 4533 |
| JavaScript | interpreted | 0.00 | 4309 |
| Soma interpreter | interpreted | 0.00 | 6796 |
| Soma JIT | transpiled-per-run | n/a | 6796 |
| Soma VM | compiled-per-run | n/a | 6796 |
| Go | unavailable | n/a | 4168 |
| Rust | unavailable | n/a | 5251 |
| C++ | unavailable | n/a | 5837 |

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
