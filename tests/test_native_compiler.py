"""Native lowering: Soma cells become specialized C++."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aot_engine.native_compiler import NativeCompiler
from benchmarks.extreme.languages.python_bench import bfs, histogram, mandelbrot, mergesort, nqueens, sieve


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


class TestNativeLowering(unittest.TestCase):
    def test_template_uses_native_representations(self):
        cpp = NativeCompiler().compile_source(render("sieve", 100, 1))
        self.assertIn("soma_count_primes", cpp)
        self.assertIn("std::vector<uint8_t>", cpp)
        self.assertNotIn("SomaBits", cpp)
        self.assertIn("SomaArena<TreeNode>", cpp)
        self.assertIn("for (", cpp)
        self.assertNotIn("std::function", cpp)
        self.assertNotIn("exceeds", cpp.lower())
        matmul = NativeCompiler().compile_source(render("matmul", 8, 1))
        self.assertIn("soma_sum_i", matmul)
        self.assertIn("soma_sum_j", matmul)
        self.assertNotIn("matrix_cell", matmul)
        trees = NativeCompiler().compile_source(render("binarytrees", 4, 1))
        self.assertEqual(trees.count("arena_TreeNode.release()"), 1)
        sort = NativeCompiler().compile_source(render("sort", 30, 1))
        self.assertIn("48271", sort)
        self.assertIn("int64_t state", sort)
        for workload in ("dijkstra", "floyd", "knapsack", "editdist", "lis", "life"):
            lowered = NativeCompiler().compile_source(render(workload, 8, 1))
            self.assertIn(f"run_{workload}", lowered)
            self.assertNotIn("cannot emit", lowered.lower())

    def test_cells_pipeline_match_and_objects_lower(self):
        cpp = NativeCompiler().compile_source(
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
"""
        )
        self.assertIn("add_one(square(", cpp)
        self.assertIn("BankAccount* acc", cpp)
        self.assertIn("soma_subject", cpp)
        if shutil.which("g++") is None and shutil.which("clang++") is None:
            return
        self.assertEqual(
            run_cpp(cpp),
            "zero\npositive\nnegative\n26\n75\nOwner Aditi\n",
        )

    def test_native_checksums_match_python_when_compiler_exists(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("no C++ compiler on PATH")
        cases = {
            "nqueens": (8, nqueens(8)),
            "sieve": (100, sieve(100)),
            "mandelbrot": (20, mandelbrot(20)),
            "bfs": (50, bfs(50)),
            "sort": (30, mergesort(30)),
            "histogram": (200, histogram(200)),
        }
        for workload, (size, expected) in cases.items():
            cpp = NativeCompiler().compile_source(render(workload, size, 1))
            output = run_cpp(cpp, optimize=False)
            checksum = float(output.split("CHECKSUM:", 1)[1].splitlines()[0])
            self.assertEqual(checksum, float(expected), workload)


def run_cpp(cpp, optimize=False):
    compiler = shutil.which("g++") or shutil.which("clang++")
    work = tempfile.mkdtemp(prefix="soma-native-test-")
    source = os.path.join(work, "program.cpp")
    binary = os.path.join(work, "program.exe" if os.name == "nt" else "program")
    with open(source, "w", encoding="utf-8") as handle:
        handle.write(cpp)
    level = "-O3" if optimize else "-O0"
    built = subprocess.run(
        [compiler, level, "-std=c++20", "-o", binary, source],
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        raise AssertionError(built.stderr or built.stdout)
    ran = subprocess.run([binary], capture_output=True, text=True)
    if ran.returncode != 0:
        raise AssertionError(ran.stderr or ran.stdout)
    return ran.stdout
