"""Soma command line. One language, one command.

On Windows, `soma run file.sm` compiles with the C# compiler that ships with
the operating system and runs on the CLR. Elsewhere it compiles with g++ or
clang++ when one is on PATH, and otherwise runs on V8 when Node.js is installed.
`--engine interpreter` walks the program in-process. `--engine vm` runs bytecode.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from lexer import Lexer
from parser import Parser
from transpiler_js import JsTranspiler, TranspileError
from aot_engine.native_compiler import NativeCompiler, NativeCompileError
from aot_engine.clr_compiler import ClrCompiler
from compiler import Compiler, CompileError
from vm import FractalVM
from core.container import FractalContainer

BANNER = """
  ____
 / ___|  ___  _ __ ___   __ _
 \\___ \\ / _ \\| '_ ` _ \\ / _` |
  ___) | (_) | | | | | | (_| |
 |____/ \\___/|_| |_| |_|\\__,_|
 Soma
 Type 'exit' to quit.
"""


def parse_source(source: str):
    return Parser(Lexer(source).tokenize()).parse()


def read_program(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return parse_source(handle.read())


def framework_compiler() -> str | None:
    """C# compiler that ships with Windows. No separate install."""
    if os.name != "nt":
        return None
    root = os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"
    for folder in ("Framework64", "Framework"):
        path = os.path.join(root, "Microsoft.NET", folder, "v4.0.30319", "csc.exe")
        if os.path.isfile(path):
            return path
    return None


def choose_engine(requested: str | None) -> str:
    if requested:
        return requested
    if framework_compiler():
        return "clr"
    if shutil.which("g++") or shutil.which("clang++"):
        return "native"
    if shutil.which("node"):
        return "jit"
    print("No Windows C# compiler, C++ compiler, or Node.js found. Running the Soma interpreter.", file=sys.stderr)
    return "interpreter"


def execute_clr(path: str) -> None:
    compiler = framework_compiler()
    if compiler is None:
        print("Soma's Windows engine needs the .NET Framework C# compiler, csc.exe.", file=sys.stderr)
        raise SystemExit(2)
    csharp = ClrCompiler().compile_program(read_program(path))
    work = os.path.join(os.path.dirname(os.path.abspath(path)) or ".", ".soma-build")
    os.makedirs(work, exist_ok=True)
    source = os.path.join(work, "Program.cs")
    binary = os.path.join(work, "Program.exe")
    with open(source, "w", encoding="utf-8") as handle:
        handle.write(csharp)
    built = subprocess.run(
        [compiler, "/nologo", "/optimize+", "/t:exe", "/out:" + binary, source],
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        print(built.stderr or built.stdout, file=sys.stderr)
        raise SystemExit(built.returncode or 1)
    completed = None
    for attempt in range(4):
        try:
            completed = subprocess.run([binary])
            break
        except OSError as error:
            if getattr(error, "winerror", None) != 4551 or attempt == 3:
                print(error, file=sys.stderr)
                raise SystemExit(1)
            time.sleep(0.2)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def execute_native(path: str) -> None:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        print("Soma native engine needs g++ or clang++ on PATH.", file=sys.stderr)
        raise SystemExit(2)
    cpp = NativeCompiler().compile_program(read_program(path))
    work = tempfile.mkdtemp(prefix="soma-native-")
    cpp_path = os.path.join(work, "program.cpp")
    binary = os.path.join(work, "program.exe" if os.name == "nt" else "program")
    with open(cpp_path, "w", encoding="utf-8") as handle:
        handle.write(cpp)
    built = subprocess.run(
        [compiler, "-O3", "-std=c++20", "-march=native", "-o", binary, cpp_path],
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        print(built.stderr or built.stdout, file=sys.stderr)
        raise SystemExit(built.returncode or 1)
    completed = subprocess.run([binary])
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def execute(path: str, engine: str, container: FractalContainer) -> None:
    if engine == "clr":
        execute_clr(path)
        return
    if engine == "native":
        execute_native(path)
        return
    ast = read_program(path)
    if engine == "jit":
        javascript = JsTranspiler(base_dir=os.path.dirname(os.path.abspath(path)) or ".").transpile(ast)
        completed = subprocess.run(["node", "-e", javascript])
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)
        return
    if engine == "vm":
        FractalVM().execute(Compiler().compile(ast))
        return
    container.interpreter.execute_ast(ast)


def start_repl(container: FractalContainer) -> None:
    print(BANNER)
    while True:
        try:
            line = input("soma> ")
            if line.strip().lower() in ("exit", "quit"):
                break
            if not line.strip():
                continue
            buffer = [line]
            if line.rstrip().endswith(":"):
                while True:
                    sub_line = input("...   ")
                    if sub_line == "":
                        break
                    buffer.append(sub_line)
            ast = parse_source("\n".join(buffer))
            result = None
            for statement in ast.statements:
                result = container.interpreter.execute_node(statement, container.interpreter.global_scope)
            if result is not None:
                print(f"=> {result}")
        except KeyboardInterrupt:
            print("\nExiting Soma.")
            break
        except Exception as error:
            print(f"Error: {error}")


def main() -> None:
    container = FractalContainer.create_default()
    parser = argparse.ArgumentParser(description="Soma language")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a .sm or .fc program")
    run_parser.add_argument("file")
    run_parser.add_argument("--engine", choices=("clr", "native", "jit", "interpreter", "vm"))
    run_parser.add_argument("--sandbox", action="store_true", help="Deny file and network access")
    run_parser.add_argument("--check", action="store_true", help="Print inferred types, then run")

    for name, help_text in (
        ("jit", "Run on V8"),
        ("vm", "Run on the Soma bytecode machine"),
        ("dis", "Print bytecode"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("file")

    for name, help_text in (
        ("emit-cpp", "Emit C++"),
        ("emit-cs", "Emit C# for the Windows CLR"),
        ("emit-js", "Emit JavaScript"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("file")
        command.add_argument("-o", "--output")

    swarm_parser = subparsers.add_parser("swarm", help="Run a Soma agent swarm")
    swarm_parser.add_argument("goal")
    subparsers.add_parser("metrics", help="Print runtime metrics")
    subparsers.add_parser("repl", help="Start the Soma REPL")

    args = parser.parse_args()
    try:
        if args.command == "run":
            if args.sandbox:
                from security.sandbox import SecuritySandboxPolicy
                container.interpreter._sandbox = SecuritySandboxPolicy.create_restricted()
            if args.check:
                from typing_engine.type_system import TypeInferenceEngine
                inferred = TypeInferenceEngine().infer_program(read_program(args.file))
                for name, inferred_type in inferred.items():
                    print(f"{name}: {inferred_type}")
            execute(args.file, choose_engine(args.engine), container)
        elif args.command == "jit":
            execute(args.file, "jit", container)
        elif args.command == "vm":
            execute(args.file, "vm", container)
        elif args.command == "dis":
            print(Compiler().compile(read_program(args.file)).disassemble(args.file))
        elif args.command == "emit-cpp":
            cpp = NativeCompiler().compile_program(read_program(args.file))
            _write_or_print(cpp, args.output, "C++")
        elif args.command == "emit-cs":
            csharp = ClrCompiler().compile_program(read_program(args.file))
            _write_or_print(csharp, args.output, "C#")
        elif args.command == "emit-js":
            javascript = JsTranspiler(
                base_dir=os.path.dirname(os.path.abspath(args.file)) or "."
            ).transpile(read_program(args.file))
            _write_or_print(javascript, args.output, "JavaScript")
        elif args.command == "swarm":
            from agentic_infra import HierarchicalSwarmCoordinator
            result = HierarchicalSwarmCoordinator(workers_count=4, assistants_per_worker=4).run_swarm(args.goal)
            print(json.dumps(result, indent=2))
        elif args.command == "metrics":
            print(json.dumps(container.metrics.snapshot(), indent=2))
        elif args.command == "repl" or len(sys.argv) == 1:
            start_repl(container)
        else:
            parser.print_help()
    except (CompileError, TranspileError, NativeCompileError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)
    finally:
        container.shutdown()


def _write_or_print(contents: str, output: str | None, label: str) -> None:
    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(contents)
        print(f"Wrote {label} to {output}")
    else:
        print(contents)


if __name__ == "__main__":
    main()
