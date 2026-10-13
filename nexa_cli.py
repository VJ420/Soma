"""
Fractal Unified Enterprise CLI.
Integrates DI Container, Circuit Breakers, Telemetry, and Multi-Backend Execution.
"""
import sys
import os
import json
import argparse
import subprocess
from lexer import Lexer
from parser import Parser
from transpiler_cpp import CppTranspiler
from transpiler_js import JsTranspiler
from aot_engine.beast_compiler import BeastNativeCompiler
from compiler import Compiler
from vm import FractalVM
from core.container import FractalContainer

BANNER = r"""
  ______               _        _ 
 |  ____|             | |      | |
 | |__ _ __ __ _  ___ | |_ __ _| |
 |  __| '__/ _` |/ __|| __/ _` | |
 | |  | | | (_| | (__ | || (_| | |
 |_|  |_|  \__,_|\___| \__\__,_|_|
 [ Enterprise Production Engine v1.0 ]
 Type 'exit' to quit. Write halwa code!
"""

def run_script(source: str, container: FractalContainer):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return container.interpreter.execute_ast(ast)

def start_repl(container: FractalContainer):
    print(BANNER)
    while True:
        try:
            line = input("fractal> ")
            if line.strip().lower() in ("exit", "quit"):
                break
            if not line.strip():
                continue

            buffer = [line]
            if line.rstrip().endswith(":"):
                while True:
                    sub_line = input("...      ")
                    if sub_line == "":
                        break
                    buffer.append(sub_line)

            source = "\n".join(buffer)
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            res = None
            for stmt in ast.statements:
                res = container.interpreter.execute_node(stmt, container.interpreter.global_scope)
            if res is not None:
                print(f"=> {res}")

        except KeyboardInterrupt:
            print("\nExiting Fractal REPL.")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    container = FractalContainer.create_default()
    parser = argparse.ArgumentParser(description="Fractal Enterprise Production System")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run via Enterprise Interpreter Engine")
    run_parser.add_argument("file", help="Path to .fc script")

    # JIT command
    jit_parser = subparsers.add_parser("jit", help="Run on V8 JIT Engine")
    jit_parser.add_argument("file", help="Path to .fc script")

    # VM command
    vm_parser = subparsers.add_parser("vm", help="Run on Bytecode Virtual Machine")
    vm_parser.add_argument("file", help="Path to .fc script")

    # Disassemble command
    dis_parser = subparsers.add_parser("dis", help="Disassemble into bytecode opcodes")
    dis_parser.add_argument("file", help="Path to .fc script")

    # Transpile to C++ command
    cpp_parser = subparsers.add_parser("emit-cpp", help="Compile to C++20")
    cpp_parser.add_argument("file", help="Path to .fc script")
    cpp_parser.add_argument("-o", "--output", help="Output C++ file path")

    # Transpile to JS command
    js_parser = subparsers.add_parser("emit-js", help="Transpile to JavaScript (Node.js/V8)")
    js_parser.add_argument("file", help="Path to .fc script")
    js_parser.add_argument("-o", "--output", help="Output JS file path")

    # Swarm Agentic command
    swarm_parser = subparsers.add_parser("swarm", help="Decompose goal into parallel subagent cells")
    swarm_parser.add_argument("goal", help="Intention or goal string")

    # Telemetry metrics command
    subparsers.add_parser("metrics", help="Print runtime telemetry metrics snapshot")

    # REPL command
    subparsers.add_parser("repl", help="Start interactive REPL")

    args = parser.parse_args()

    try:
        if args.command == "run":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            run_script(code, container)

        elif args.command == "jit":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            ast = Parser(tokens).parse()
            js_code = JsTranspiler().transpile(ast)
            subprocess.run(["node", "-e", js_code])

        elif args.command == "vm":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            ast = Parser(tokens).parse()
            chunk = Compiler().compile(ast)
            vm = FractalVM()
            vm.execute(chunk)

        elif args.command == "dis":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            ast = Parser(tokens).parse()
            chunk = Compiler().compile(ast)
            print(chunk.disassemble(args.file))

        elif args.command == "emit-cpp":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            ast = Parser(tokens).parse()
            cpp_code = BeastNativeCompiler().compile_to_native_cpp(ast)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(cpp_code)
                print(f"Successfully generated C++ in: {args.output}")
            else:
                print(cpp_code)

        elif args.command == "emit-js":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            tokens = Lexer(code).tokenize()
            ast = Parser(tokens).parse()
            js_code = JsTranspiler().transpile(ast)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(js_code)
                print(f"Successfully generated JS in: {args.output}")
            else:
                print(js_code)

        elif args.command == "swarm":
            from agentic_infra import ParallelCellEngine
            engine = ParallelCellEngine()
            result = engine.run_goal(args.goal)
            print(json.dumps(result, indent=2))

        elif args.command == "metrics":
            snap = container.metrics.snapshot()
            print(json.dumps(snap, indent=2))

        elif args.command == "repl" or len(sys.argv) == 1:
            start_repl(container)

        else:
            parser.print_help()

    finally:
        container.shutdown()

if __name__ == "__main__":
    main()
