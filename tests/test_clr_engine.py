"""Windows CLR lowering: Soma cells become C# and match the Python checksums."""
import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aot_engine.clr_compiler import ClrCompiler
from benchmarks.extreme.languages.python_bench import WORKLOADS
from soma_cli import framework_compiler


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE = os.path.join(ROOT, "benchmarks", "extreme", "languages", "soma_bench.sm.in")


def render(workload, size, iterations):
    with open(TEMPLATE, encoding="utf-8") as handle:
        source = handle.read()
    return (
        source.replace("{{WORKLOAD}}", workload)
        .replace("{{SIZE}}", str(size))
        .replace("{{ITERATIONS}}", str(iterations))
    )


def run_csharp(source: str) -> str:
    compiler = framework_compiler()
    if compiler is None:
        raise unittest.SkipTest("csc.exe is not on this machine")
    work = os.path.join(ROOT, ".soma-build")
    os.makedirs(work, exist_ok=True)
    path = os.path.join(work, "Program.cs")
    binary = os.path.join(work, "Program.exe")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(source)
    built = subprocess.run(
        [compiler, "/nologo", "/optimize+", "/t:exe", "/out:" + binary, path],
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        raise AssertionError(built.stderr or built.stdout)
    ran = None
    for attempt in range(4):
        try:
            ran = subprocess.run([binary], capture_output=True, text=True)
            break
        except OSError as error:
            if getattr(error, "winerror", None) != 4551 or attempt == 3:
                raise
            time.sleep(0.2)
    if ran.returncode != 0:
        raise AssertionError(ran.stderr or ran.stdout or f"exit {ran.returncode}")
    return ran.stdout


class TestClrLowering(unittest.TestCase):
    def test_cells_pipeline_match_and_objects(self):
        if framework_compiler() is None:
            self.skipTest("csc.exe is not on this machine")
        csharp = ClrCompiler().compile_source(
            """
classify(n):
  match n:
    0: "zero"
    x when x > 0: "positive"
    _: "negative"
square(x): x * x
add_one(x): x + 1
piped = 5 -> square -> add_one
BankAccount(owner, balance):
  deposit(amount):
    balance = balance + amount
  current(): balance
acc: BankAccount("Aditi", 50)
acc.deposit(25)
print(classify(0))
print(classify(3))
print(classify(0 - 1))
print(str(piped))
print(str(acc.current()))
print("Owner {acc.owner}")
print(str(int((0 - 5) / 2)))
wide(x, y): x * y
print(str(wide(100000, 100000)))
"""
        )
        self.assertIn("soma_count_primes", csharp)
        self.assertIn("SomaArena", csharp)
        self.assertEqual(
            run_csharp(csharp),
            "zero\npositive\nnegative\n26\n75\nOwner Aditi\n-2\n10000000000\n",
        )

    def test_checksums_match_python(self):
        if framework_compiler() is None:
            self.skipTest("csc.exe is not on this machine")
        sizes = {
            "nqueens": 8,
            "mandelbrot": 16,
            "matmul": 8,
            "lcs": 24,
            "sieve": 100,
            "nbody": 8,
            "binarytrees": 6,
            "bfs": 40,
            "sort": 32,
            "stencil": 8,
            "histogram": 200,
            "dijkstra": 16,
            "floyd": 12,
            "knapsack": 24,
            "editdist": 16,
            "lis": 48,
            "life": 12,
        }
        for workload, size in sizes.items():
            csharp = ClrCompiler().compile_source(render(workload, size, 1))
            output = run_csharp(csharp)
            checksum = float(output.split("CHECKSUM:", 1)[1].splitlines()[0])
            expected = float(WORKLOADS[workload](size))
            self.assertEqual(checksum, expected, workload)


if __name__ == "__main__":
    unittest.main()
