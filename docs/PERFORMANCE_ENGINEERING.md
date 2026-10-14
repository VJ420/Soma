# Soma performance

Soma is one language. `soma run file.sm` executes it on V8 when Node.js is installed. That is the fast path. It sits in the same class as JavaScript and, on numeric loops, ahead of CPython.

It does not beat Rust or C++. Older tables that said it did were typed in, not measured. Those numbers have been removed.

## Measured check

`python benchmarks/extreme/run_benchmarks.py` runs Soma, Python, JavaScript, Go, Rust, and C++ on one machine and drops any timing whose checksum disagrees.

A local Mandelbrot check, 40 by 40, one iteration:

| Runtime | Kernel time |
|---|---:|
| Soma on V8 (`soma run`) | 0.57 ms |
| JavaScript | 0.63 ms |
| Python 3.12 | 10.60 ms |
| Soma interpreter (`--engine interpreter`) | 1,649 ms |

## The three engines

- **V8** is what `soma run` uses. Soma source is translated to JavaScript and Node runs it.
- **Interpreter** (`--engine interpreter`) walks the program in Python. It is the slow path. Use it for `spawn`.
- **Bytecode** (`--engine vm`) runs inside Python. It now supports indexing, `match`, `and`/`or`, and methods that update closed-over fields.

`soma emit-cpp` writes C++ source. That file does nothing until a C++ compiler builds it, and building it is not a measured win over Rust.
