# Soma Language Specification & Architecture Standard
**Version:** 2.0.0-LTS  
**Conceived and Crafted in India**  
Created & Designed by **[Vighnesh Jha](https://github.com/VJ420)** ([@VJ420](https://github.com/VJ420))  
**Core Axiom:** *The Universal Cell — Infinite Depth from a Single Rule*

---

## 1. Axiomatic Foundation: The Universal Cell

Soma eliminates the cognitive dissonance of classical languages which force developers to choose between variables, functions, closures, classes, modules, and processes.

In Soma, **everything is a Cell**.

A Cell is defined formally as a 4-tuple:
$$\mathcal{C} = \langle \mathcal{I}, \mathcal{S}, \mathcal{B}, \mathcal{E} \rangle$$
Where:
- $\mathcal{I}$ is the input parameter space (empty for variables, non-empty for functions/constructors).
- $\mathcal{S}$ is the lexical scope binding environment.
- $\mathcal{B}$ is the sequence of executable evaluations.
- $\mathcal{E}$ is the exported structural interface (the final evaluated expression or explicit inner cell bindings).

```
+--------------------------------------------------------------+
|                        UNIVERSAL CELL                        |
|                                                              |
|   Inputs (I) -----> [ Lexical Scope (S) ]                    |
|                            |                                 |
|                            v                                 |
|                   [ Body Evaluation (B) ]                    |
|                            |                                 |
|                            v                                 |
|   Export (E) <----- [ State / Return ]                       |
+--------------------------------------------------------------+
```

### Unification Matrix

| Classical Paradigm | Classical Syntax (Python/Rust/Go) | Soma Equivalent |
| :--- | :--- | :--- |
| **Variable** | `x = 42` | `x: 42` |
| **Function** | `def f(x): return x + 1` | `f(x): x + 1` |
| **Object / Class** | `class BankAccount: def __init__(self, bal): ...` | `BankAccount(bal): deposit(a): bal = bal + a` |
| **Module / Namespace** | `module Math { const PI = 3.14; }` | `Math: pi: 3.14` |
| **Process / Fiber** | `go func() { ... }()` | `spawn: ...` |

---

## 2. Syntax & Grammar Specifications

A cell is the whole declaration. There is no `def`, `class`, `self`, or `return`.

### Grammar EBNF (Core Rules)

```ebnf
Program         ::= Statement* EOF
Statement       ::= CellDef | Assignment | Pipeline | MatchStmt | ControlStmt | Expr NEWLINE
CellDef         ::= IDENTIFIER ("(" ParamList? ")")? ":" Block
ParamList       ::= IDENTIFIER ("," IDENTIFIER)*
Block           ::= NEWLINE INDENT Statement+ DEDENT
Assignment      ::= (IDENTIFIER | MemberAccess) ("=" | ":") Expr
Pipeline        ::= Expr ("->" Expr)+
MatchStmt       ::= "match" Expr ":" NEWLINE INDENT MatchCase+ DEDENT
MatchCase       ::= Pattern ("when" Expr)? ":" Block
ControlStmt     ::= IfStmt | WhileStmt | ForStmt | SpawnStmt
SpawnStmt       ::= "spawn" ":" Block
```

### Key Syntactic Innovations

1. **Zero `self` / `this`**: Members are closed over lexically in the cell scope.
2. **Zero `return`**: The tail expression of any cell or block automatically forms its result.
3. **Pipelining (`->`)**: Natural left-to-right function chaining:
   ```soma
   data -> filter_valid -> transform -> persist
   ```
4. **String Interpolation**: Directly embedded without extra prefixes:
   ```soma
   "Order ID {order.id} processed in {elapsed_ms}ms"
   ```

---

## 3. Execution

Soma has one syntax. `.sm` is the canonical extension. `.fc` still loads. `soma run` compiles with `g++` or `clang++` when one is on PATH, and otherwise translates to JavaScript for Node.

```
[ Source (.sm) ] -> [ Lexer ] -> [ Parser ]
                                    |
          +------------+------------+------------+
          |            |            |            |
       Native         V8      Interpreter     VM
       C++ -O3      Node.js     AST walk    bytecode
```

- **Native** (`aot_engine/native_compiler.py`): cells become C++. Integers that fit are 32-bit, wide products stay 64-bit, boolean arrays are bytes, a separable triple loop becomes a double reduction, the textbook sieve becomes the odd-only sieve, and object cells come from an arena that rewinds. This is the engine measured in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md).
- **V8** (`transpiler_js.py`): JavaScript executed by Node. Fallback when no C++ compiler is installed.
- **Interpreter** (`runtime_engine/enterprise_interpreter.py`): in-process AST walk. The REPL uses it. `spawn` runs here.
- **Bytecode** (`compiler.py`, `vm.py`): in-process stack machine.

`soma --check` prints inferred types and then runs. `--sandbox` denies file, network, and subprocess access. The measured ranking is one run on one machine. It is not a property of every program.

---

## 4. Agent swarm

`soma swarm "goal"` is a Python coordinator (`agentic_infra.py`) around Soma cells. It splits a goal into worker cells and assistant cells and runs the leaves on threads. It is not a second language, and it is not the benchmark in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md).

Inside a program, `spawn` starts a block and the cell that started it waits for that block to finish.

---

## 5. Security & Sandbox Invariant Enforcement

With `--sandbox`, a program runs under `security/sandbox.py`:
- `FILE_SYSTEM`: Read, write, or isolated access.
- `NETWORK`: Inbound, outbound, or air-gapped isolation.
- `EXEC`: Subprocess spawning permissions.
- Violations trigger an immediate, non-recoverable `SecurityViolationError` before arbitrary kernel syscalls execute.
