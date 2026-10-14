<div align="center">

# Soma (`.sm`)
### *The Universal Cell Programming Language*

**High-Performance General-Purpose Language for Distributed Systems and Autonomous Workloads**  
**Conceived and Crafted in India**  
Created by **[Vighnesh Jha](https://github.com/VJ420)** ([@VJ420](https://github.com/VJ420))

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Build Status](https://img.shields.io/badge/Tests-24%20Passing-brightgreen.svg?style=flat-square)]()
[![Architecture](https://img.shields.io/badge/Architecture-Universal%20Cell-9cf.svg?style=flat-square)]()
[![Execution](https://img.shields.io/badge/Execution-V8%20%2B%20interpreter%20%2B%20VM-orange.svg?style=flat-square)]()

<br/>

> **"One Primitive. Zero Ceremony. One command."**  
> Soma unifies variables, functions, objects, modules, and concurrent fibers into one construct: **The Universal Cell**.  
> `soma run` executes that source on V8. The same file can run on the interpreter or the bytecode machine.

---

</div>

## Table of Contents

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

You write concise domain code. `python soma_cli.py run file.sm` translates it to JavaScript and runs it on Node. `--engine interpreter` and `--engine vm` run the same source in-process.

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
`soma run file.sm` executes the program on V8 when Node.js is installed. The same source can also run on the in-process interpreter (`--engine interpreter`) or the bytecode machine (`--engine vm`). C++ emission is a separate backend and is not a claim of beating Rust.

### 6. First-Class Autonomous Agent Swarms (SMAA-V2)
Built-in 3-tier hierarchical decomposition (Master $\to$ Regional Workers $\to$ Micro-Assistants) across 16 concurrent leaf fibers without GIL bottlenecks.

### 7. Capability-Based Sandbox Security
Deterministic runtime security policy engine that restricts filesystem, network, and subprocess access at the VM boundary.

### 8. Enterprise Fault Tolerance & Observability
- Integrated **Circuit Breakers** (`CLOSED` $\to$ `OPEN` $\to$ `HALF_OPEN`) with automatic dead-letter failure isolation.
- Asynchronous, non-blocking **JSON structured telemetry** and metrics collection.

---

## Measured performance

Earlier tables that showed Soma beating Rust used numbers that were typed in, not measured. The current suite is `benchmarks/extreme/`. It runs the same algorithms in Soma, Python, JavaScript, Go, Rust, and C++, checks a checksum, and keeps only timings from that run.

On the measured run, Soma's V8 path is faster than CPython and slower than Go, Rust, and C++. The in-process interpreter is much slower than CPython. Reproduce with:

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

Soma provides 4 seamless execution tiers for every stage of development and deployment:

```
┌────────────────────────────────────────────────────────┐
│                    Soma Source (.sm)                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Indentation-Aware Lexer & Parser           │
│        Slotted Frozen AST Nodes (@dataclass(slots))    │
└───────────────┬─────────────────────────┬──────────────┘
                │                         │
                ▼                         ▼
┌───────────────────────────────┐ ┌──────────────────────┐
│  Tier 1: Interactive Engine   │ │  Tier 2: Bytecode VM │
│  - Instant REPL & Debugging   │ │  - Compact OpCodes   │
│  - Circuit-Breaker Guarded    │ │  - Stack Execution   │
└───────────────────────────────┘ └──────────────────────┘
                │                         │
                ▼                         ▼
┌───────────────────────────────┐ ┌──────────────────────┐
│  Tier 3: V8 engine            │ │  Tier 4: C++ emitter │
│  - soma run, via Node         │ │  - emits C++ source  │
│  - same class as JavaScript   │ │  - compile it yourself│
└───────────────────────────────┘ └──────────────────────┘
```

- **Tier 1: Interactive Engine**: Direct AST execution equipped with circuit breakers (`CLOSED` $\to$ `OPEN` $\to$ `HALF_OPEN`), recursion depth limiters, and real-time structured telemetry.
- **Tier 2: Bytecode Virtual Machine**: Slotted variable indexing, constant pooling, and stack-frame dispatch for lightweight embedded execution.
- **Tier 3: V8 engine**: `soma run` translates Soma to JavaScript and executes it with Node. This is the fast path. It is in the same performance class as JavaScript, not Rust.
- **Tier 4: C++ emitter**: `soma emit-cpp` writes C++ source. A C++ compiler has to build that source before it can run. Emitting C++ is not itself a measured win over Rust.

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

- **Tier 1: Master Orchestrator Cell**: Ingests macro program intentions, calculates global load topology, and assigns regional chunks to Regional Worker Cells.
- **Tier 2: Regional Worker Cells**: Act as autonomous partition supervisors, continuously monitoring latency and subdividing workloads into micro-slices for their dedicated assistants.
- **Tier 3: Micro-Assistant Cells**: 16 concurrent leaf fibers executing lock-free vector kernels sized precisely to fit inside hardware CPU L1/L2 caches.
- The swarm is a Python coordinator around Soma cells. It decomposes a goal and runs the leaves on threads. It is not a separate language.

```powershell
python soma_cli.py swarm "Analyze 5M telemetry records concurrently"
```

---

## Security & Sandbox Model

The sandbox is opt-in. `python soma_cli.py run file.sm --sandbox` loads `SecuritySandboxPolicy` and denies file reads, file writes, network, and subprocesses. A violation raises `SecurityViolationException`. A normal `soma run` does not enable the sandbox, so programs can still read modules and write files.

---

## Project Architecture

```
soma-lang/
├── ast_nodes.py              # Slotted, frozen AST dataclass nodes
├── lexer.py                  # Indentation-aware lexer (INDENT/DEDENT/NEWLINE)
├── parser.py                 # Recursive descent parser with pattern matching
├── bytecode.py               # VM Bytecode instruction set and constants
├── compiler.py               # AST to Bytecode compiler
├── vm.py                     # Stack-based Virtual Machine execution engine
├── transpiler_js.py          # High-velocity compiler engine
├── transpiler_cpp.py         # Standard C++ emitter
├── soma_cli.py               # Unified command-line interface
├── swarm_core.py             # 3-Tier Autonomous agent swarm execution engine
├── agentic_infra.py          # 3-Tier Swarm intention decomposition engine
│
├── aot_engine/
│   └── beast_compiler.py    # Native C++20 / SIMD AVX2 AOT compiler
│
├── concurrency/
│   └── circuit_breaker.py   # Circuit breaker state machine (CLOSED/OPEN/HALF_OPEN)
│
├── config/
│   └── settings.py          # Typed configuration subsystem (Zero magic numbers)
│
├── core/
│   ├── container.py         # IoC / Dependency Injection Container
│   └── interfaces.py        # Abstract execution strategies & contracts
│
├── runtime_engine/
│   └── enterprise_interpreter.py # Enterprise slotted interpreter strategy
│
├── security/
│   └── sandbox.py           # Capability-based security sandbox policy engine
│
├── telemetry/
│   └── logger.py            # Asynchronous non-blocking structured JSON logger
│
├── typing_engine/
│   └── type_system.py       # Bidirectional Hindley-Milner type inference
│
├── std/                     # Standard Library
│   ├── math.fc              # Math kernels, constants, and trigonometry
│   ├── array.fc             # High-throughput array transformations
│   └── string.fc            # Fast string manipulation & formatting
│
├── examples/                # Production code samples (.sm)
│   ├── 01_hello_cells.sm
│   ├── 02_oop_without_boilerplate.sm
│   ├── 03_pipeline_and_match.sm
│   ├── 04_mandelbrot_extreme.sm
│   └── 05_parallel_agent_swarm.sm
│
├── benchmarks/              # Empirical cross-domain benchmark suites
│   ├── cross_domain_benchmark.py
│   ├── hard_math_benchmark.py
│   └── cross_domain_extreme_results.json
│
└── docs/                    # Architectural documentation
    ├── SPECIFICATION.md
    ├── PERFORMANCE_ENGINEERING.md
    ├── STDLIB_REFERENCE.md
    └── BENCHMARK_METHODOLOGY.md
```

---

## Quickstart & Installation

### Prerequisites
- **Python 3.12+** (Core runtime and CLI)
- **Node.js 18+** (High-velocity execution engine)
- *Optional:* Clang / GCC with C++20 support (Native SIMD compilation)

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
# 1. Run on V8. This is the normal command.
python soma_cli.py run examples/01_hello_cells.sm

# 2. Same V8 path, explicit.
python soma_cli.py jit examples/04_mandelbrot_extreme.sm

# 3. In-process interpreter. Required for spawn.
python soma_cli.py run examples/01_hello_cells.sm --engine interpreter

# 4. Bytecode machine.
python soma_cli.py vm examples/01_hello_cells.sm

# 5. Disassemble Code into Bytecode OpCodes
python soma_cli.py dis examples/01_hello_cells.sm

# 6. Emit C++ source. A C++ compiler still has to build it.
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

Soma includes a comprehensive test suite covering all architectural subsystems:

```bash
python -m unittest discover tests
```

*Status: 24/24 tests passing.*

To run the automated empirical benchmark matrix:
```bash
python benchmarks/cross_domain_benchmark.py
```

---

## Documentation Suite

- [**Language Specification (`docs/SPECIFICATION.md`)**](docs/SPECIFICATION.md): Formal EBNF grammar, cell model semantics, and lexical rules.
- [**Performance Engineering (`docs/PERFORMANCE_ENGINEERING.md`)**](docs/PERFORMANCE_ENGINEERING.md): In-depth hardware breakdown of cache-line packing, AVX2 SIMD vectorization, and escape analysis.
- [**Standard Library Reference (`docs/STDLIB_REFERENCE.md`)**](docs/STDLIB_REFERENCE.md): API documentation for `std/math.fc`, `std/array.fc`, and `std/string.fc`.
- [**Benchmark Methodology (`docs/BENCHMARK_METHODOLOGY.md`)**](docs/BENCHMARK_METHODOLOGY.md): Scientific protocols, timing resolution, and validation invariants.

---

## Author & License

Soma is conceived, architected, and maintained by **Vighnesh Jha**.  
GitHub: [github.com/VJ420](https://github.com/VJ420)  
Repository: [github.com/VJ420/Soma](https://github.com/VJ420/Soma)

Released under the **MIT License**.  
Copyright © 2026 Vighnesh Jha.
