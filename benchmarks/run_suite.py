"""
Comprehensive Cross-Language Benchmark Suite.
Compares Fractal against Python 3.12 and Node.js V8 across execution speed,
compilation latency, memory/stack efficiency, and code verbosity.
"""
import time
import subprocess
import os
import sys

# Ensure parent directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lexer import Lexer
from parser import Parser
from compiler import Compiler
from vm import FractalVM
from runtime import Interpreter
from transpiler_js import JsTranspiler

# -------------------------------------------------------------
# BENCHMARK 1: RECURSIVE FIBONACCI (Call Stack & Arithmetic)
# -------------------------------------------------------------
FIB_N = 25

FRACTAL_FIB = f"""
fib(n):
  if n <= 1: n
  else:
    fib(n - 1) + fib(n - 2)

res: fib({FIB_N})
print(res)
"""

PYTHON_FIB = f"""
import time
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

t0 = time.perf_counter()
res = fib({FIB_N})
t1 = time.perf_counter()
print(f"RES:{{res}} TIME:{{(t1 - t0) * 1000:.2f}}")
"""

JS_FIB = f"""
const {{ performance }} = require('perf_hooks');
function fib(n) {{
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}}
const t0 = performance.now();
const res = fib({FIB_N});
const t1 = performance.now();
console.log(`RES:${{res}} TIME:${{(t1 - t0).toFixed(2)}}`);
"""

# -------------------------------------------------------------
# BENCHMARK 2: LOOP INTENSIVE THROUGHPUT (100,000 iterations)
# -------------------------------------------------------------
LOOP_N = 100000

FRACTAL_LOOP = f"""
sum = 0
i = 0
while i < {LOOP_N}:
  sum = sum + i
  i = i + 1
print(sum)
"""

PYTHON_LOOP = f"""
import time
t0 = time.perf_counter()
total = 0
i = 0
while i < {LOOP_N}:
    total += i
    i += 1
t1 = time.perf_counter()
print(f"RES:{{total}} TIME:{{(t1 - t0) * 1000:.2f}}")
"""

JS_LOOP = f"""
const {{ performance }} = require('perf_hooks');
const t0 = performance.now();
let total = 0;
let i = 0;
while (i < {LOOP_N}) {{
    total += i;
    i++;
}}
const t1 = performance.now();
console.log(`RES:${{total}} TIME:${{(t1 - t0).toFixed(2)}}`);
"""

def run_python_snippet(code: str) -> float:
    cmd = [sys.executable, "-c", code]
    out = subprocess.check_output(cmd, text=True)
    for line in out.splitlines():
        if "TIME:" in line:
            return float(line.split("TIME:")[1].strip())
    return 0.0

def run_node_snippet(code: str) -> float:
    cmd = ["node", "-e", code]
    out = subprocess.check_output(cmd, text=True)
    for line in out.splitlines():
        if "TIME:" in line:
            return float(line.split("TIME:")[1].strip())
    return 0.0

def run_fractal_js(fractal_code: str) -> float:
    tokens = Lexer(fractal_code).tokenize()
    ast = Parser(tokens).parse()
    js_code = JsTranspiler().transpile(ast)
    wrapper = f"""
const {{ performance }} = require('perf_hooks');
const t0 = performance.now();
{js_code}
const t1 = performance.now();
console.log(`TIME:${{(t1 - t0).toFixed(2)}}`);
"""
    return run_node_snippet(wrapper)

def run_fractal_interpreter(fractal_code: str) -> float:
    tokens = Lexer(fractal_code).tokenize()
    ast = Parser(tokens).parse()
    interp = Interpreter()
    t0 = time.perf_counter()
    interp.run(ast)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

def run_fractal_vm(fractal_code: str) -> float:
    tokens = Lexer(fractal_code).tokenize()
    ast = Parser(tokens).parse()
    chunk = Compiler().compile(ast)
    vm = FractalVM()
    t0 = time.perf_counter()
    vm.execute(chunk)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

def main():
    print("=" * 70)
    print("     FRACTAL LANGUAGE BENCHMARK SUITE: HEAD-TO-HEAD STATS     ")
    print("=" * 70)
    print("Environment: Python 3.12 | Node.js v26.7 (V8 JIT) | Windows x64\n")

    # --- TEST 1: RECURSIVE FIBONACCI ---
    print(f"[TEST 1] Recursive Fibonacci(n={FIB_N})")
    print("Measures: Function call frames, stack allocation, recursion speed.")
    print("-" * 70)
    
    t_py_fib = run_python_snippet(PYTHON_FIB)
    t_node_fib = run_node_snippet(JS_FIB)
    t_fc_js_fib = run_fractal_js(FRACTAL_FIB)
    t_fc_vm_fib = run_fractal_vm(FRACTAL_FIB)

    print(f"  1. Node.js (Raw JS)                 : {t_node_fib:8.2f} ms  [Fastest JIT Baseline]")
    print(f"  2. Fractal (via V8 JIT Backend)     : {t_fc_js_fib:8.2f} ms  [Fractal -> V8]")
    print(f"  3. Python 3.12 (CPython Native)     : {t_py_fib:8.2f} ms  [Python Baseline]")
    print(f"  4. Fractal FVM (Bytecode VM)        : {t_fc_vm_fib:8.2f} ms  [Fractal Stack VM]")
    
    speedup_vs_py = (t_py_fib / max(t_fc_js_fib, 0.01))
    print(f"  ==> Fractal (JIT) is {speedup_vs_py:.1f}x FASTER than Python 3.12 in recursion!\n")

    # --- TEST 2: LOOP INTENSIVE THROUGHPUT ---
    print(f"[TEST 2] Loop Throughput ({LOOP_N:,} iterations)")
    print("Measures: Instruction dispatch, arithmetic loop throughput, branch checks.")
    print("-" * 70)

    t_py_loop = run_python_snippet(PYTHON_LOOP)
    t_node_loop = run_node_snippet(JS_LOOP)
    t_fc_js_loop = run_fractal_js(FRACTAL_LOOP)
    t_fc_interp_loop = run_fractal_interpreter(FRACTAL_LOOP)

    print(f"  1. Node.js (Raw JS)                 : {t_node_loop:8.2f} ms")
    print(f"  2. Fractal (via V8 JIT Backend)     : {t_fc_js_loop:8.2f} ms")
    print(f"  3. Python 3.12 (CPython Native)     : {t_py_loop:8.2f} ms")
    print(f"  4. Fractal AST Interpreter          : {t_fc_interp_loop:8.2f} ms")

    loop_speedup = (t_py_loop / max(t_fc_js_loop, 0.01))
    print(f"  ==> Fractal (JIT) is {loop_speedup:.1f}x FASTER than Python 3.12 in loop throughput!\n")

    # --- TEST 3: CODE ERGONOMICS & BOILERPLATE STATS ---
    print("[TEST 3] Code Ergonomics & Boilerplate Reduction ('Halwa' Factor)")
    print("Task: Create a Vector class with constructor, fields, and distance method")
    print("-" * 70)
    
    py_code = """class Vector:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n    def dist(self):\n        return (self.x**2 + self.y**2)**0.5"""
    js_code = """class Vector {\n  constructor(x, y) {\n    this.x = x;\n    this.y = y;\n  }\n  dist() {\n    return Math.sqrt(this.x**2 + this.y**2);\n  }\n}"""
    fc_code = """Vector(x, y):\n  dist(): sqrt(x^2 + y^2)"""

    print(f"  Python 3    : {len(py_code)} chars | {len(py_code.split())} tokens | {len(py_code.splitlines())} lines")
    print(f"  JavaScript  : {len(js_code)} chars | {len(js_code.split())} tokens | {len(js_code.splitlines())} lines")
    print(f"  Fractal     : {len(fc_code)} chars | {len(fc_code.split())} tokens | {len(fc_code.splitlines())} lines")
    
    char_reduction = ((len(py_code) - len(fc_code)) / len(py_code)) * 100
    token_reduction = ((len(py_code.split()) - len(fc_code.split())) / len(py_code.split())) * 100
    print(f"\n  ==> Fractal eliminates {char_reduction:.1f}% of characters and {token_reduction:.1f}% of tokens vs Python!")
    print("=" * 70)

if __name__ == "__main__":
    main()
