"""Local interpreter-versus-bytecode loop.

Archived. This is not the cross-language ranking. That ranking is docs/MEASURED_PERFORMANCE.md.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
from lexer import Lexer
from parser import Parser
from compiler import Compiler
from vm import FractalVM
from runtime import Interpreter

BENCHMARK_CODE = """
# Compute 100,000 loop operations
sum = 0
i = 0
while i < 10000:
  sum = sum + i
  i = i + 1

print("Benchmark loop result:", sum)
"""

def run_benchmarks():
    print("=" * 55)
    print("         SOMA INTERPRETER VS BYTECODE LOOP         ")
    print("=" * 55)

    tokens = Lexer(BENCHMARK_CODE).tokenize()
    ast = Parser(tokens).parse()

    # 1. AST Interpreter
    interp = Interpreter()
    t0 = time.perf_counter()
    interp.run(ast)
    t1 = time.perf_counter()
    ast_time = (t1 - t0) * 1000
    print(f"[AST Interpreter] Execution time : {ast_time:8.2f} ms")

    # 2. Bytecode Compiler + VM
    t_comp_0 = time.perf_counter()
    chunk = Compiler().compile(ast)
    t_comp_1 = time.perf_counter()
    comp_time = (t_comp_1 - t_comp_0) * 1000

    vm = FractalVM()
    t_vm_0 = time.perf_counter()
    vm.execute(chunk)
    t_vm_1 = time.perf_counter()
    vm_time = (t_vm_1 - t_vm_0) * 1000

    print(f"[Bytecode Compiler] Compile time  : {comp_time:8.2f} ms")
    print(f"[Fractal Bytecode VM] Exec time   : {vm_time:8.2f} ms")
    print(f"Bytecode VM Speedup Ratio         : {ast_time / max(vm_time, 0.001):8.2f}x faster")
    print("=" * 55)

if __name__ == "__main__":
    run_benchmarks()
