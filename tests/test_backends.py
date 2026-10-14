"""Soma backend parity: one language on the interpreter, V8, and the VM."""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lexer import Lexer
from parser import Parser
from compiler import Compiler, CompileError
from vm import FractalVM
from transpiler_js import JsTranspiler
from core.container import FractalContainer
from security.sandbox import SecuritySandboxPolicy, SecurityViolationException


def parse(source):
    return Parser(Lexer(source).tokenize()).parse()


def run_vm(source):
    return FractalVM().execute(Compiler().compile(parse(source)))


def run_interpreter(source):
    container = FractalContainer.create_default()
    try:
        return container.interpreter.execute_ast(parse(source))
    finally:
        container.shutdown()


class TestSomaBackends(unittest.TestCase):
    def test_vm_index_and_short_circuit(self):
        result = run_vm("""
items: [10, 20, 30]
items[1] = 99
kept: false
if false and items[1]:
  kept = true
items[1]
""")
        self.assertEqual(result, 99)

    def test_vm_match_and_object_methods(self):
        result = run_vm("""
classify(n):
  match n:
    0: "zero"
    x when x > 0: "positive"
    _: "negative"

Counter(initial):
  val = initial
  inc():
    val = val + 1
  get(): val

box: Counter(10)
box.inc()
box.inc()
[classify(0), classify(4), classify(0 - 3), box.get()]
""")
        self.assertEqual(result, ["zero", "positive", "negative", 12])

    def test_vm_rejects_spawn(self):
        with self.assertRaises(CompileError):
            Compiler().compile(parse("spawn:\n  1\n"))

    def test_v8_match_and_collections(self):
        javascript = JsTranspiler().transpile(parse("""
classify(n):
  match n:
    0: "zero"
    x when x > 0: "positive"
    _: "negative"

double(n): n * 2
values: map([1, 2, 3], double)
print(classify(0))
print(values[2])
"""))
        completed = subprocess.run(
            ["node", "-e", javascript],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.splitlines(), ["zero", "6"])
        account = JsTranspiler().transpile(parse("""
BankAccount(balance):
  deposit(amount):
    balance = balance + amount
  get(): balance

acc: BankAccount(50)
acc.deposit(25)
print(acc.get())
"""))
        completed = subprocess.run(["node", "-e", account], check=True, capture_output=True, text=True)
        self.assertEqual(completed.stdout.strip(), "75")

    def test_interpreter_map_filter_push_and_sandbox(self):
        self.assertEqual(
            run_interpreter("""
double(n): n * 2
keep(n): n > 1
push(map([1, 2, 3], double), 9)
"""),
            [2, 4, 6, 9],
        )
        container = FractalContainer.create_default()
        container.interpreter._sandbox = SecuritySandboxPolicy.create_restricted()
        try:
            with self.assertRaises(SecurityViolationException):
                container.interpreter.execute_ast(parse('write_file("secret.txt", "no")'))
        finally:
            container.shutdown()


if __name__ == "__main__":
    unittest.main()
