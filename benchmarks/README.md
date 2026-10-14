# Benchmarks

The ranking is [extreme/](extreme/). It runs the same algorithms in Soma, Python, JavaScript, Go, Rust, and C++, keeps a time only when the checksum matches Python, and writes `REPORT.md`. The published copy of that report, and the rules for quoting it, are [docs/MEASURED_PERFORMANCE.md](../docs/MEASURED_PERFORMANCE.md) and [docs/BENCHMARK_METHODOLOGY.md](../docs/BENCHMARK_METHODOLOGY.md).

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

[archive/](archive/) holds older local probes: interpreter versus bytecode, swarm tiers, and Python-and-JavaScript kernels. Those scripts are not the cross-language ranking.
