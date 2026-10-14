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

The published run is GitHub Actions run [38517496358](https://github.com/VJ420/Soma/actions/runs/38517496358), commit `468ec56`, on an AMD EPYC 9V45, 14 Oct 2026. It covers 17 tasks. An earlier 11-task run, [38512994105](https://github.com/VJ420/Soma/actions/runs/38512994105), was an AMD EPYC 7763 and measured 0.69×. A later run on a different processor is a new measurement. Compare rows inside one run.

`benchmarks/archive/` holds older local probes. They time Python, JavaScript, the interpreter, or the swarm. They are not the ranking. The ranking is only the extreme suite.
