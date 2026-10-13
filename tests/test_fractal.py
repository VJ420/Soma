"""
Fractal Comprehensive Automated Test Suite.
Validates syntax, semantics, recursive modularity, concurrency, and virtual machine.
"""
import unittest
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lexer import Lexer
from parser import Parser
from runtime import Interpreter
from compiler import Compiler
from vm import FractalVM

def eval_fractal(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    interp = Interpreter()
    return interp.run(ast), interp

class TestFractalLanguage(unittest.TestCase):

    def test_arithmetic_precedence(self):
        res, _ = eval_fractal("2 + 3 * 4 ^ 2")
        self.assertEqual(res, 2 + 3 * (4 ** 2))

    def test_recursive_modularity(self):
        code = """
math:
  square(x): x * x
  cube(x): x * square(x)

math.cube(3)
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, 27)

    def test_objects_and_mutation(self):
        code = """
Counter(initial):
  val = initial
  inc():
    val = val + 1
  get(): val

c: Counter(10)
c.inc()
c.inc()
c.get()
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, 12)

    def test_pipeline(self):
        code = """
double(x): x * 2
add5(x): x + 5

10 -> double -> add5
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, 25)

    def test_string_interpolation(self):
        code = """
name: "Fractal"
level: 9000
greeting: "Welcome to {name}! Power is over {level}!"
greeting
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, "Welcome to Fractal! Power is over 9000!")

    def test_pattern_matching_with_guards(self):
        code = """
classify(n):
  match n:
    0: "zero"
    x when x > 0: "positive: {x}"
    _: "negative"

[classify(0), classify(42), classify(-5)]
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, ["zero", "positive: 42", "negative"])

    def test_list_indexing_and_mutation(self):
        code = """
lst: [10, 20, 30]
lst[1] = 99
lst[1]
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, 99)

    def test_concurrency_channel(self):
        code = """
ch: channel()
spawn:
  42 -> ch.send

ch.recv()
"""
        res, _ = eval_fractal(code)
        self.assertEqual(res, 42)

    def test_vm_execution(self):
        code = """
square(n): n * n
square(8)
"""
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        chunk = Compiler().compile(ast)
        vm = FractalVM()
        res = vm.execute(chunk)
        self.assertEqual(res, 64)

if __name__ == "__main__":
    unittest.main()
