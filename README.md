<div align="center">

# Soma (`.sm`)
### *The Universal Cell Programming Language*

**High-Performance General-Purpose Language for Distributed Systems and Autonomous Workloads**  
**Conceived and Crafted in India**  
Created by **[Vighnesh Jha](https://github.com/VJ420)** ([@VJ420](https://github.com/VJ420))

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Build Status](https://img.shields.io/badge/Tests-unittest-brightgreen.svg?style=flat-square)]()
[![Architecture](https://img.shields.io/badge/Architecture-Universal%20Cell-9cf.svg?style=flat-square)]()
[![Execution](https://img.shields.io/badge/Execution-Native%20C%2B%2B%20when%20available-orange.svg?style=flat-square)]()

<br/>

> **"One Primitive. Zero Ceremony. One command."**  
> Soma unifies variables, functions, objects, modules, and concurrent fibers into one construct: **The Universal Cell**.  
> `soma run` compiles that source to native code when a C++ compiler is installed, and runs it on V8 otherwise. The same file can run on the interpreter or the bytecode machine.

---

</div>

## If you just arrived

Soma is one language. A value, a function, and an object are the same kind of cell. There is no `self`, no `class`, and no `return`: the tail expression is the result.

```soma
square(x): x * x
5 -> square -> print
```

`soma run file.sm` compiles that file to C++ when `g++` or `clang++` is installed, and runs it on Node otherwise.

On the published run Soma was first of six languages. Geometric-mean kernel time was **0.84×** the fastest other language across 17 tasks, and all 17 checksums matched. The machine was an AMD EPYC 9V45 on 14 Oct 2026. The full table is [docs/MEASURED_PERFORMANCE.md](docs/MEASURED_PERFORMANCE.md). The task list, the cold-start times, and where Soma still trails are on that page.

## Table of Contents

- [If you just arrived](#if-you-just-arrived)
- [Why Soma?](#why-soma)
- [The Architectural Axiom: The Universal Cell](#the-architectural-axiom-the-universal-cell)
- [Key Features](#key-features)
- [Measured performance](#measured-performance)
- [Syntax & Ergonomics: Maximum Signal, Zero Boilerplate](#syntax--ergonomics-maximum-signal-zero-boilerplate)
- [Unified Execution Pipeline](#unified-execution-pipeline)
- [Autonomous Agent Swarm Infrastructure (SMAA-V2)](#autonomous-agent-swarm-infrastructure-smaa-v2)
- [Security & Sandbox Model](#security--sandbox-model)
- [Project Architecture](#project-architecture)
- [Quickstart & Installation](#quickstart--installation)
- [Unified CLI Reference](#unified-cli-reference)
- [Verification & Quality Assurance](#verification--quality-assurance)
- [Documentation Suite](#documentation-suite)
- [Author & License](#author--license)

---

## Why Soma?

Modern software development is fragmented across artificial syntactic categories. A typical codebase forces developers to constantly switch mental models:
- A single primitive is a variable.
- Reusable logic is a function or method.
- State and behavior encapsulation requires a `class` or `struct`.
- Organization across files requires separate module namespaces.
- Parallelism requires distinct thread pools, channels, or event loops.

This creates massive syntactic tax, repetitive boilerplate (`self`, `__init__`, lifetime annotations, reference wrappers), and architectural friction.

**Soma resolves this fragmentation through Recursive Modularity.**  
The name **Soma** comes from the biological core—the cell body from which all living structures grow. In Soma, every single language element is an instance of one self-similar construct: **The Universal Cell**.

You write concise domain code. `python soma_cli.py run file.sm` compiles it with `g++` or `clang++` when one of those is on PATH. Otherwise it translates the same source to JavaScript and runs it on Node. `--engine interpreter` and `--engine vm` run it in-process.

---

## The Architectural Axiom: The Universal Cell

Every entity in Soma is a recursive lexical Cell:

$$\mathcal{C} = \langle \mathcal{I}, \mathcal{S}, \mathcal{B}, \mathcal{E} \rangle$$

Where:
- $\mathcal{I}$ is the formal parameter space (empty for variables, non-empty for functions/objects).
- $\mathcal{S}$ is the lexical binding environment.
- $\mathcal{B}$ is the sequence of evaluated operations.
- $\mathcal{E}$ is the exported structural interface (the evaluated tail value or inner member cells).

### Complete Paradigm Unification

| Semantic Role | Conventional Languages (Python / Go / Rust) | Soma (`.sm`) Equivalent |
| :--- | :--- | :--- |
| **Variable** | `x = 42` | `x: 42` |
| **Pure Function** | `def square(x): return x * x` | `square(x): x * x` |
| **Stateful Class / Object** | `class BankAccount: def __init__(self, b): self.b = b` | `BankAccount(b): deposit(a): b = b + a` |
| **Module / Namespace** | `namespace Math { const PI = 3.14; }` | `Math: pi: 3.14` |
| **Concurrent Fiber / Actor** | `go func() { ... }()` | `spawn: ...` |

---

## Key Features

### 1. The Universal Cell Architecture
Variables, functions, objects, packages, and concurrent processes are all unified into a single primitive: the Cell. Master one rule, and you understand the entire language.

### 2. Maximum Signal, Zero Boilerplate
- **No `def`, `fn`, or `function`**: Callables are simply parameterized cells.
- **No `class` or `struct`**: Objects are stateful cells with nested member cells.
- **No `__init__` or constructors**: Parameters passed to a cell automatically form its persistent state.
- **No `self` or `this`**: Scope is closed over lexically with zero pointer indirection.
- **No explicit `return`**: The tail expression of any block forms its evaluated export.

### 3. Native Dataflow Pipelines (`->`)
Chain operations left-to-right in natural reading order without deeply nested function calls:
```soma
records -> filter_valid -> transform -> persist
```

### 4. Expressive Pattern Matching with Guards
Pattern match against constants, ranges, and predicates with clean `match / when` syntax:
```soma
route_status(code):
    match code:
        200: "SUCCESS"
        404: "NOT_FOUND"
        err when err >= 500: "UPSTREAM_GATEWAY_ERROR_{err}"
        _: "UNKNOWN"
```

### 5. One language, one run command
`soma run file.sm` compiles to native code when `g++` or `clang++` is installed. The same source can also run on V8 (`--engine jit`), the in-process interpreter (`--engine interpreter`), or the bytecode machine (`--engine vm`). The measured ranking of that native path is in [docs/MEASURED_PERFORMANCE.md](docs/MEASURED_PERFORMANCE.md).

### 6. First-Class Autonomous Agent Swarms (SMAA-V2)
`soma swarm` splits a goal into a master cell, four worker cells, and sixteen assistant cells, then runs the leaves on Python threads.

### 7. Capability-Based Sandbox Security
`soma run file.sm --sandbox` denies filesystem, network, and subprocess access. A normal run does not enable it.

### 8. Enterprise Fault Tolerance & Observability
- Integrated **Circuit Breakers** (`CLOSED` $\to$ `OPEN` $\to$ `HALF_OPEN`) with automatic dead-letter failure isolation.
- Asynchronous, non-blocking **JSON structured telemetry** and metrics collection.

---

## Measured performance

Older tables that showed Soma beating Rust were typed in. Those numbers are gone. The current suite is `benchmarks/extreme/`. It runs the same algorithms in Soma, Python, JavaScript, Go, Rust, and C++, checks a checksum, and keeps only timings from that run.

On the published run (GitHub Actions 38517496358, commit `468ec56`, AMD EPYC 9V45, 14 Oct 2026) the native Soma path was first of the six across 17 tasks. Geometric-mean kernel time was **0.84×** the fastest other language, **0.79×** C++, and **0.71×** Rust. All 17 checksums matched. The task table is in [docs/MEASURED_PERFORMANCE.md](docs/MEASURED_PERFORMANCE.md).

| Place | Runtime | Geomean vs fastest other |
|---|---|---:|
| 1 | Soma native | 0.84× |
| 2 | C++ | 1.06× |
| 3 | Rust | 1.18× |
| 4 | Go | 1.60× |
| 5 | JavaScript | 3.46× |
| 6 | Python | 62.78× |

That ranking is one machine and one suite. Longest increasing subsequence, knapsack, and Life still trail the leader on that run. An earlier 11-task run on an AMD EPYC 7763 measured 0.69×. Reproduce with:

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

---

## Syntax & Ergonomics: Maximum Signal, Zero Boilerplate

### 1. Object Definition and State Mutation

#### Python 3.12 (Verbose, Repetitive)
```python
class Account:
    def __init__(self, owner: str, balance: float):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount: float) -> None:
        self.balance += amount

    def summary(self) -> str:
        return f"{self.owner}: {self.balance}"
```

#### Rust (Complex Struct, Impl, and Mutability Ceremony)
```rust
struct Account {
    owner: String,
    balance: f64,
}

impl Account {
    pub fn new(owner: String, balance: f64) -> Self {
        Self { owner, balance }
    }
    pub fn deposit(&mut self, amount: f64) {
        self.balance += amount;
    }
    pub fn summary(&self) -> String {
        format!("{}: {}", self.owner, self.balance)
    }
}
```

#### Soma (`.sm`) (Direct, Expressive, 70%+ Less Code)
```soma
Account(owner, balance):
    deposit(amount):
        balance = balance + amount
    summary():
        "{owner}: {balance}"
```

### 2. Functional Data Pipelines
```soma
# Left-to-right processing pipeline without nested parentheses
records -> validate_input -> normalize -> persist_database
```

### 3. Pattern Matching with Guards
```soma
route_response(status):
    match status:
        200: "SUCCESS"
        404: "RESOURCE_NOT_FOUND"
        err when err >= 500: "UPSTREAM_FAILURE_{err}"
        _: "UNKNOWN_STATUS"
```

---

## Unified Execution Pipeline

Soma has one syntax and four ways to run it. `soma run` picks the first one that the machine can build.

```
┌────────────────────────────────────────────────────────┐
│                    Soma Source (.sm)                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Indentation-Aware Lexer & Parser           │
└───────────────┬────────────────────┬───────────────────┘
                │                    │
                ▼                    ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│  Native (default)         │ │  V8, if no C++ compiler  │
│  Soma cells to C++        │ │  --engine jit            │
│  g++ or clang++ -O3       │ │                          │
└───────────────────────────┘ └──────────────────────────┘
                │                    │
                ▼                    ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│  Interpreter              │ │  Bytecode machine        │
│  --engine interpreter     │ │  --engine vm             │
│  spawn, REPL, tracebacks  │ │  in-process              │
└───────────────────────────┘ └──────────────────────────┘
```

- **Native**: `aot_engine/native_compiler.py` lowers cells to C++ and `soma run` builds that with `-O3 -std=c++20 -march=native`. This is the engine in the measured ranking.
- **V8**: `transpiler_js.py` emits JavaScript and Node runs it. This is the fallback when no C++ compiler is installed.
- **Interpreter**: walks the AST in Python. The REPL uses it. `spawn` is defined here.
- **Bytecode**: `compiler.py` and `vm.py` run a stack machine in Python.

---

## Autonomous Agent Swarm Infrastructure (SMAA-V2)

Soma is engineered from first principles for hierarchical, autonomous agent systems. Rather than a flat, naive dispatch loop, Soma utilizes a **3-Tier Recursive Swarm Topology**:

```
[ Master Orchestrator Cell ]
          │
          ├── Worker Cell 0 ──── [ Micro-Assistant 0.0 ] ─── (Leaves process
          │                 ──── [ Micro-Assistant 0.1 ]       L1/L2 cache-sized
          │                 ──── [ Micro-Assistant 0.2 ]       vector sub-slices)
          │                 ──── [ Micro-Assistant 0.3 ]
          │
          ├── Worker Cell 1 ──── [ Micro-Assistants 1.0 .. 1.3 ]
          ├── Worker Cell 2 ──── [ Micro-Assistants 2.0 .. 2.3 ]
          └── Worker Cell 3 ──── [ Micro-Assistants 3.0 .. 3.3 ]
```

- **Master**: takes the goal and builds the worker tree.
- **Workers**: four regional cells, each with four assistants.
- **Assistants**: sixteen leaves, run with a thread pool.
- The swarm is a Python coordinator. It is not a separate language, and it is not the ranking in [docs/MEASURED_PERFORMANCE.md](docs/MEASURED_PERFORMANCE.md).

```powershell
python soma_cli.py swarm "Analyze 5M telemetry records concurrently"
```

---

## Security & Sandbox Model

The sandbox is opt-in. `python soma_cli.py run file.sm --sandbox` loads `SecuritySandboxPolicy` and denies file reads, file writes, network, and subprocesses. A violation raises `SecurityViolationException`. A normal `soma run` does not enable the sandbox, so programs can still read modules and write files.

---

## Project Architecture

These are the paths a visitor needs. The other files implement them.

| Path | What it is |
|---|---|
| `soma_cli.py` | The command. `soma run`, `soma repl`, `soma swarm`, `soma --check`. |
| `aot_engine/native_compiler.py` | The measured engine. Soma cells lowered to C++. |
| `examples/` | Programs you can run. `.sm` is the usual extension. `.fc` still loads. |
| `benchmarks/extreme/` | The only cross-language ranking. Report: `benchmarks/extreme/REPORT.md`. |
| `docs/` | Specification, the measured table, how the compiler lowers code, the standard library, and the benchmark rules. |
| `std/` | `math`, `array`, and `string`. |
| `benchmarks/archive/` | Older local probes. They are not the ranking. |

```
soma-lang/
├── soma_cli.py                 # CLI. fractal_cli.py and nexa_cli.py forward here
├── lexer.py                    # Indentation-aware lexer
├── parser.py                   # Parser, including match and pipelines
├── ast_nodes.py                # AST
├── aot_engine/native_compiler.py
├── transpiler_js.py            # V8 fallback
├── runtime.py                  # In-process interpreter entry used by the CLI
├── runtime_engine/enterprise_interpreter.py
├── compiler.py                 # Bytecode compiler
├── bytecode.py
├── vm.py                       # Bytecode machine
├── transpiler_cpp.py           # Older C++ emitter. The measured engine is native_compiler.py
├── typing_engine/type_system.py
├── security/sandbox.py
├── swarm_core.py               # Thread-pool swarm
├── swarm_v2_hierarchical.py
├── agentic_infra.py
├── concurrency/circuit_breaker.py
├── telemetry/logger.py
├── config/settings.py
├── core/
├── std/                        # math.fc, array.fc, string.fc
├── examples/                   # 01–05 .sm, plus the longer .fc demos
├── benchmarks/extreme/         # The ranking
├── benchmarks/archive/         # Older probes
├── tests/
└── docs/
```

---

## Quickstart & Installation

### Prerequisites
- **Python 3.12+** (CLI, parser, and the in-process engines)
- **g++ or clang++** with C++20 (the default `soma run` engine, and the measured one)
- **Node.js 18+** (fallback when no C++ compiler is installed)

### Clone & Setup
```bash
git clone https://github.com/VJ420/Soma.git
cd Soma
```

### Run Hello Cells
```bash
python soma_cli.py run examples/01_hello_cells.sm
```

---

## Unified CLI Reference

```bash
# 1. Native when g++ or clang++ exists, otherwise V8.
python soma_cli.py run examples/01_hello_cells.sm

# 2. Force V8.
python soma_cli.py run examples/04_mandelbrot_extreme.sm --engine jit

# 3. In-process interpreter. The REPL uses this engine. spawn is defined here.
python soma_cli.py run examples/01_hello_cells.sm --engine interpreter

# 4. Bytecode machine.
python soma_cli.py vm examples/01_hello_cells.sm

# 5. Print bytecode.
python soma_cli.py dis examples/01_hello_cells.sm

# 6. Emit the same C++ the native engine compiles, without running it.
python soma_cli.py emit-cpp examples/04_mandelbrot_extreme.sm -o kernel.cpp

# 7. Run the agent swarm
python soma_cli.py swarm "Analyze 5M telemetry records concurrently"

# 8. Inspect runtime metrics
python soma_cli.py metrics

# 9. Launch the REPL
python soma_cli.py repl
```

---

## Verification & Quality Assurance

```bash
python -m unittest discover tests
```

The cross-language ranking is `benchmarks/extreme/`. Scripts in `benchmarks/archive/` are older local probes.

```bash
python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results
```

---

## Documentation Suite

- [**Language Specification (`docs/SPECIFICATION.md`)**](docs/SPECIFICATION.md): Cell model, grammar, and the four engines.
- [**Measured performance (`docs/MEASURED_PERFORMANCE.md`)**](docs/MEASURED_PERFORMANCE.md): The published ranking, per-task times, and what the compiler rewrote.
- [**Performance engineering (`docs/PERFORMANCE_ENGINEERING.md`)**](docs/PERFORMANCE_ENGINEERING.md): Integer width, the separable product, the odd sieve, and the arena.
- [**Standard Library Reference (`docs/STDLIB_REFERENCE.md`)**](docs/STDLIB_REFERENCE.md): `std/math.fc`, `std/array.fc`, and `std/string.fc`.
- [**Benchmark methodology (`docs/BENCHMARK_METHODOLOGY.md`)**](docs/BENCHMARK_METHODOLOGY.md): Checksums, clocks, and what is not a ranking.
- [**What changed (`CHANGELOG.md`)**](CHANGELOG.md): The native compiler, the two measured runs, and how the repository is laid out.

---

## Author & License

Soma is conceived, architected, and maintained by **Vighnesh Jha**.  
GitHub: [github.com/VJ420](https://github.com/VJ420)  
Repository: [github.com/VJ420/Soma](https://github.com/VJ420/Soma)

Released under the **MIT License**.  
Copyright © 2026 Vighnesh Jha.
