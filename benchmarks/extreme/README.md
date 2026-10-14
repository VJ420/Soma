# Soma extreme cross-language benchmarks

This suite compares actual Soma programs with equivalent Python, JavaScript,
Go, Rust, and C++ implementations. It replaces the repository's older
hardcoded reference numbers with measurements produced on one machine.

## What is measured

- Seven deterministic workloads spanning factorial/exponential, cubic,
  quadratic, and near-linear complexity classes.
- End-to-end elapsed time, including CLI and runtime startup.
- Zero-iteration cold start, build/transpile cost, source or artifact size,
  and peak resident memory on Linux.
- Three input sizes for empirical complexity fitting.
- Three independent process samples after one warm-up.

Every implementation prints a checksum. A timing is discarded if it times out,
crashes, or disagrees with the Python reference (with a tight tolerance for the
floating-point N-body simulation).

## Reproduce

The full suite needs Python, Node.js, Go, Rust, and a C++20 compiler:

```bash
python benchmarks/extreme/run_benchmarks.py \
  --output benchmarks/extreme/results
```

No local installation is required when using the
`Extreme cross-language benchmarks` GitHub Actions workflow.

For a local smoke test with installed runtimes:

```bash
python benchmarks/extreme/run_benchmarks.py \
  --workload mandelbrot \
  --runtime Python \
  --runtime JavaScript \
  --runtime "Soma interpreter" \
  --runtime "Soma JIT" \
  --max-sizes 1 \
  --repetitions 1
```

Generated artifacts:

- `results/raw_results.json`: environment, builds, raw samples, checksums, and
  unsupported cases.
- `results/REPORT.md`: generated analysis.
- `REPORT.md`: latest generated report at a stable path.

## Interpretation

Soma JIT is Soma source translated by `transpiler_js.py` and then executed by
Node/V8. Raw JavaScript is a separate baseline. Soma VM cases that require
unsupported AST operations are labeled unsupported rather than silently
dropped. Compare values within one workflow run because GitHub runner hardware
can change between runs.
