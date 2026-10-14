# How Soma benchmarks are measured

The ranking in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md) comes from `benchmarks/extreme/run_benchmarks.py`.

The harness:

- Runs the same algorithm in Soma, Python, JavaScript, Go, Rust, and C++.
- Times the kernel with a clock inside the program. Startup is a separate zero-iteration measurement.
- Keeps a time only when the checksum matches Python. N-body uses a relative tolerance of 1e-8 and an absolute tolerance of 1e-7. Stencil uses 1e-6 and 1e-5. The other tasks require an exact match.
- Records the machine, the compiler flags, and the raw samples.
- Leaves a language blank when its compiler is not installed. It does not fill the cell in.
- Runs each kernel on one thread. Inner iterations are 10 for Python, 20 for JavaScript, and 100 for Go, Rust, C++, and Soma native, so a short kernel is not lost in the clock.

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

The published run is GitHub Actions run 38512994105 on an AMD EPYC 7763. A later run on a different processor is a new measurement. Do not average it with this one.

`benchmarks/cross_domain_benchmark.py` and `benchmarks/hard_math_benchmark.py` time Python and JavaScript only. They are not a Soma-versus-Rust result. `benchmark.py` times the in-process interpreter against the bytecode machine on one loop. It is not the cross-language ranking.
