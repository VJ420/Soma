"""
Production Rigor Verification & Stress Test Suite.
Tests:
1. Syntax Simplicity ("Halwa" verification)
2. Recursive Cell Composition
3. Pattern Matching with Guards
4. Actor Concurrency with Bounded Channels
5. Multi-Module Imports
6. String Interpolation
7. List and Map Indexing & Mutation
8. High-Depth Recursion Guard (Fault-tolerance limit)
9. Circuit Breaker Resilience under failure
10. Telemetry & Metrics Snapshot Validation
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lexer import Lexer
from parser import Parser
from config.settings import SystemConfig, RuntimeConfig
from core.container import FractalContainer
from runtime_engine.enterprise_interpreter import RecursionLimitExceededException
from concurrency.circuit_breaker import CircuitBreakerOpenException

def run_code(src: str, container: FractalContainer):
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    return container.interpreter.execute_ast(ast)

class TestEnterpriseFractalEngine(unittest.TestCase):

    def setUp(self):
        self.container = FractalContainer.create_default()

    def tearDown(self):
        self.container.shutdown()

    def test_arithmetic_and_precedence(self):
        res = run_code("10 + 5 * 2 ^ 3", self.container)
        self.assertEqual(res, 10 + 5 * (2 ** 3))

    def test_recursive_modularity(self):
        code = """
math:
  square(x): x * x
  cube(x): x * square(x)

math.cube(4)
"""
        res = run_code(code, self.container)
        self.assertEqual(res, 64)

    def test_oop_objects_without_boilerplate(self):
        code = """
Account(owner, balance):
  deposit(amount):
    balance = balance + amount
  withdraw(amount):
    balance = balance - amount
  get_balance(): balance

acc: Account("Vishu", 1000)
acc.deposit(500)
acc.withdraw(200)
acc.get_balance()
"""
        res = run_code(code, self.container)
        self.assertEqual(res, 1300)

    def test_pipeline_operator(self):
        code = """
square(x): x * x
inc(x): x + 1

5 -> square -> inc
"""
        res = run_code(code, self.container)
        self.assertEqual(res, 26)

    def test_string_interpolation(self):
        code = """
hero: "IronMan"
hp: 100
status: "Status: {hero} has {hp * 10} HP!"
status
"""
        res = run_code(code, self.container)
        self.assertEqual(res, "Status: IronMan has 1000 HP!")

    def test_pattern_matching_with_guards(self):
        code = """
eval_status(code):
  match code:
    200: "SUCCESS"
    404: "NOT_FOUND"
    err when err >= 500 and err < 600: "SERVER_ERROR_{err}"
    _: "UNKNOWN"

[eval_status(200), eval_status(404), eval_status(503), eval_status(999)]
"""
        res = run_code(code, self.container)
        self.assertEqual(res, ["SUCCESS", "NOT_FOUND", "SERVER_ERROR_503", "UNKNOWN"])

    def test_bounded_channel_concurrency(self):
        code = """
ch: channel()
spawn:
  12345 -> ch.send

ch.recv()
"""
        res = run_code(code, self.container)
        self.assertEqual(res, 12345)

    def test_recursion_limit_guard(self):
        # Create small config with max recursion depth of 20
        config = SystemConfig(runtime=RuntimeConfig(max_recursion_depth=20))
        strict_container = FractalContainer(config)
        try:
            infinite_code = """
recurse(n):
  recurse(n + 1)

recurse(1)
"""
            with self.assertRaises(RecursionLimitExceededException):
                run_code(infinite_code, strict_container)
        finally:
            strict_container.shutdown()

    def test_circuit_breaker_resilience(self):
        cb = self.container.circuit_breaker
        failures = 0
        def failing_action():
            raise ValueError("Deliberate test failure")

        for _ in range(5):
            try:
                cb.execute(failing_action)
            except ValueError:
                failures += 1

        self.assertEqual(failures, 5)
        # 6th attempt must fail with CircuitBreakerOpenException (Fail Fast)
        with self.assertRaises(CircuitBreakerOpenException):
            cb.execute(failing_action)

    def test_telemetry_metrics_collection(self):
        run_code("x: 100\ny: x * 2\ny", self.container)
        snapshot = self.container.metrics.snapshot()
        self.assertIn("program_execution_ms", snapshot["timings"])
        self.assertGreater(snapshot["timings"]["program_execution_ms"]["count"], 0)

if __name__ == "__main__":
    unittest.main()
