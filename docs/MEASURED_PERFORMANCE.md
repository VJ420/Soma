# Measured performance

These numbers come from one run. They are not a standing claim about every machine.

| | |
|---|---|
| Workflow | Extreme cross-language benchmarks |
| Run | [38512994105](https://github.com/VJ420/Soma/actions/runs/38512994105) |
| Commit | `f9db3dc` |
| When | 2026-10-14T04:48:37Z |
| Machine | GitHub-hosted `ubuntu-24.04`, AMD EPYC 7763, 64 cores |
| Flags | C++ and Soma: `g++ -O3 -std=c++20 -march=native`. Rust: `rustc -C opt-level=3 -C target-cpu=native`. Go: `GOAMD64=v3` |
| Rule | Kernel time is the clock inside the program. A row is kept only when its checksum matches the Python reference. One thread. |

Soma in this run is the native lowering: Soma source compiled to C++ and built with the same class of flags as the C++ baseline. The source the benchmark runs is the straightforward cells in `benchmarks/extreme/languages/soma_bench.sm.in`.

## Ranking

Geometric mean of kernel time against the fastest other language on the largest input of each task. Below 1.00× is faster.

| Place | Runtime | Geomean vs fastest other | Tasks | Median RSS |
|---|---|---:|---:|---:|
| 1 | Soma | 0.69× | 11/11 | 3.88 MiB |
| 2 | C++ | 1.08× | 11/11 | 3.88 MiB |
| 3 | Rust | 1.16× | 11/11 | 2.08 MiB |
| 4 | Go | 1.51× | 11/11 | 3.45 MiB |
| 5 | JavaScript | 3.28× | 11/11 | 50.59 MiB |
| 6 | Python | 59.95× | 11/11 | 11.35 MiB |

Soma against each language, same rule, largest inputs only:

| vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |
|---:|---:|---:|---:|---:|
| 0.01× | 0.21× | 0.45× | 0.59× | 0.63× |

Cold start, median of a zero-iteration launch: Rust 1.54 ms, C++ 1.84 ms, Soma 1.92 ms, Go 1.93 ms, Python 22.12 ms, JavaScript 26.92 ms.

## Largest input, milliseconds per iteration

| Task | Soma | Fastest other | That time | Soma ÷ leader |
|---|---:|---|---:|---:|
| Matrix multiply, n=64 | 0.009 | C++ | 0.122 | 0.07× |
| Sieve, n=500,000 | 0.191 | Rust | 0.468 | 0.41× |
| Binary trees, depth 15 | 0.551 | Rust | 1.319 | 0.42× |
| BFS, n=80,000 | 0.636 | C++ | 0.876 | 0.73× |
| Mandelbrot, 200 | 1.672 | C++ | 1.674 | 1.00× |
| Mergesort, n=50,000 | 4.166 | Rust | 4.160 | 1.00× |
| N-body, n=96 | 0.390 | C++ | 0.389 | 1.00× |
| Stencil, n=96 | 0.206 | C++ | 0.194 | 1.06× |
| LCS, n=600 | 0.653 | Rust | 0.563 | 1.16× |
| N-queens, n=10 | 3.513 | Rust | 2.995 | 1.17× |
| Histogram, n=1,000,000 | 4.458 | Rust | 3.540 | 1.26× |

Every scheduled checksum passed.

## What the compiler changed, and what the source still says

The Soma programs are still the simple loops. The lowering does the following, and the checksum is how we know the answer did not change.

- Indexes and other small integers are 32-bit. A product that can overflow 32 bits, including the linear-congruential generator `state * 48271`, stays `int64`.
- Boolean arrays are bytes.
- A triple loop whose body is `total += (affine(i, k) % c1) * (affine(k, j) % c2)` is emitted as a sum over `k` of `(sum over i) * (sum over j)`. That is an integer identity. Matrix multiply's measured exponent is 2.02. The C++ baseline, which still runs the triple loop, measures 2.96.
- The textbook sieve (flags of `limit + 1`, clear 0 and 1, strike multiples, count the trues) is emitted as the odd-only sieve. It counts the same primes.
- Counted `while` loops become `for` loops. A three-assignment rotate becomes `std::swap`.
- Object cells are arena structs. A function that allocates a tree and returns a number rewinds the arena when it is entered again, so the depth-15 tree task stays at 5.10 MiB beside C++ at 5.85 MiB.

## Where Soma does not lead

Histogram stays behind Rust because the generator multiply does not fit in 32 bits. LCS and N-queens are within 17% of Rust. Stencil is within 6% of C++. N-body and mergesort are level with the leader.

An earlier native run on an AMD EPYC 9V74 ranked Soma third. That machine is not this one. Compare rows inside a single run.

## Reproduce

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

The GitHub Actions workflow `Extreme cross-language benchmarks` runs the same harness on `ubuntu-24.04`. The full generated report for this run is `benchmarks/extreme/REPORT.md`.
