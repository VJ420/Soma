# How Soma benchmarks are measured

Compare languages only with `benchmarks/extreme/run_benchmarks.py`.

That harness:

- Runs the same algorithm in Soma, Python, JavaScript, Go, Rust, and C++.
- Checks a checksum before it keeps a timing.
- Records the machine, toolchain versions, and raw samples in `raw_results.json`.
- Leaves Go, Rust, and C++ blank when those compilers are not installed. It does not fill them in.

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

`benchmarks/cross_domain_benchmark.py` and `benchmarks/hard_math_benchmark.py` time Python and JavaScript only. They are not a Soma-versus-Rust result.
