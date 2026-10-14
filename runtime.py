"""
Fractal Runtime Engine.
Executes the Fractal AST honoring Recursive Modularity, dynamic scoping,
first-class pipelines, and uniform Cell instances.
"""
import os
import pathlib
import math
import time
import threading
import queue
from typing import Any, Dict, List, Optional
from ast_nodes import (
    ASTNode, ProgramNode, CellDefNode, AssignmentNode, MemberAssignmentNode,
    PipelineNode, CallNode, MemberAccessNode, BinaryOpNode, UnaryOpNode,
    LiteralNode, IdentifierNode, ListNode, MapNode, IfNode, ForNode, WhileNode,
    UseNode, MatchCaseNode, MatchNode, SpawnNode, IndexAccessNode, IndexAssignmentNode
)

class FractalCellInstance:
    """Represents an instantiated Cell (Object, Module, Scope)."""
    def __init__(self, name: str, env: 'Environment'):
        self.name = name
        self.env = env

    def get_member(self, member: str) -> Any:
        if member in self.env.bindings:
            return self.env.bindings[member]
        raise AttributeError(f"Cell '{self.name}' has no member '{member}'")

    def set_member(self, member: str, value: Any):
        self.env.bindings[member] = value

    def __repr__(self):
        keys = list(self.env.bindings.keys())
        return f"<Cell '{self.name}': {keys}>"

class FractalCallableCell:
    """Represents a Cell that can be called with arguments."""
    def __init__(self, name: str, params: List[str], body: List[ASTNode], closure_env: 'Environment'):
        self.name = name
        self.params = params
        self.body = body
        self.closure_env = closure_env

    def call(self, args: List[Any], interpreter: 'Interpreter') -> Any:
        if len(args) != len(self.params):
            raise TypeError(f"Cell '{self.name}' expects {len(self.params)} args ({self.params}), got {len(args)}")
        
        call_env = Environment(parent=self.closure_env)
        for param_name, arg_val in zip(self.params, args):
            call_env.set(param_name, arg_val)

        last_val = None
        has_sub_cells = False

        for stmt in self.body:
            if isinstance(stmt, CellDefNode):
                has_sub_cells = True
            last_val = interpreter.execute(stmt, call_env)

        # If it defined sub-cells and the last statement was a definition, return the instance!
        if has_sub_cells and (not self.body or isinstance(self.body[-1], CellDefNode)):
            return FractalCellInstance(name=self.name, env=call_env)

        return last_val

    def __repr__(self):
        return f"<CellFunction '{self.name}({', '.join(self.params)})'>"

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined variable or cell '{name}'")

    def set(self, name: str, value: Any):
        self.bindings[name] = value

    def assign(self, name: str, value: Any):
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        # If not found anywhere, define in current
        self.bindings[name] = value

class FractalChannel:
    """Channel for message-passing concurrency between fibers and cells."""
    def __init__(self):
        self._q = queue.Queue()

    def send(self, val):
        self._q.put(val)
        return val

    def recv(self, timeout=None):
        return self._q.get(timeout=timeout)

    def empty(self):
        return self._q.empty()

    def __repr__(self):
        return f"<Channel pending={self._q.qsize()}>"

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self._init_builtins()

    def _init_builtins(self):
        def _print(*args):
            formatted = [str(a) if not isinstance(a, bool) else ("true" if a else "false") for a in args]
            print(*formatted)
            return args[-1] if args else None

        def _sqrt(x): return math.sqrt(x)
        def _sin(x): return math.sin(x)
        def _cos(x): return math.cos(x)
        def _abs(x): return abs(x)
        def _len(x): return len(x)
        def _range(*args): return list(range(*args))
        def _str(x): return str(x)
        def _int(x): return int(x)
        def _float(x): return float(x)
        def _type(x): return type(x).__name__
        def _time(): return time.time()
        def _sleep(s): time.sleep(s); return None
        def _channel(): return FractalChannel()
        
        def _map(iterable, fn):
            res = []
            for item in iterable:
                if hasattr(fn, "call"):
                    res.append(fn.call([item], self))
                elif callable(fn):
                    res.append(fn(item))
                else:
                    raise TypeError("Target of map must be callable")
            return res

        def _filter(iterable, fn):
            res = []
            for item in iterable:
                keep = False
                if hasattr(fn, "call"):
                    keep = bool(fn.call([item], self))
                elif callable(fn):
                    keep = bool(fn(item))
                if keep:
                    res.append(item)
            return res

        def _push(lst, item):
            lst.append(item)
            return lst

        def _read_file(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        def _write_file(path, content):
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(content))
            return len(str(content))

        self.global_env.set("print", _print)
        self.global_env.set("read_file", _read_file)
        self.global_env.set("write_file", _write_file)
        self.global_env.set("sqrt", _sqrt)
        self.global_env.set("sin", _sin)
        self.global_env.set("cos", _cos)
        self.global_env.set("abs", _abs)
        self.global_env.set("len", _len)
        self.global_env.set("range", _range)
        self.global_env.set("str", _str)
        self.global_env.set("int", _int)
        self.global_env.set("float", _float)
        self.global_env.set("type", _type)
        self.global_env.set("time", _time)
        self.global_env.set("sleep", _sleep)
        self.global_env.set("channel", _channel)
        self.global_env.set("map", _map)
        self.global_env.set("filter", _filter)
        self.global_env.set("push", _push)

    def run(self, program: ProgramNode):
        result = None
        for stmt in program.statements:
            result = self.execute(stmt, self.global_env)
        return result

    def execute(self, node: ASTNode, env: Environment) -> Any:
        if isinstance(node, LiteralNode):
            return node.value

        if isinstance(node, IdentifierNode):
            return env.get(node.name)

        if isinstance(node, ListNode):
            return [self.execute(elem, env) for elem in node.elements]

        if isinstance(node, MapNode):
            return {self.execute(k, env): self.execute(v, env) for k, v in node.pairs}

        if isinstance(node, CellDefNode):
            if node.params is not None:
                # Parameterized / Callable Cell (Function, Method, or Constructor)
                callable_cell = FractalCallableCell(
                    name=node.name,
                    params=node.params,
                    body=node.body,
                    closure_env=env
                )
                env.set(node.name, callable_cell)
                return callable_cell
            else:
                # 0-parameter cell: can be simple value or nested module/object
                if len(node.body) == 1 and not isinstance(node.body[0], CellDefNode):
                    val = self.execute(node.body[0], env)
                    env.set(node.name, val)
                    return val
                else:
                    # Module / Namespace cell: create nested environment
                    child_env = Environment(parent=env)
                    last_val = None
                    for child_stmt in node.body:
                        last_val = self.execute(child_stmt, child_env)
                    instance = FractalCellInstance(name=node.name, env=child_env)
                    env.set(node.name, instance)
                    return instance

        if isinstance(node, AssignmentNode):
            val = self.execute(node.value, env)
            env.assign(node.target, val)
            return val

        if isinstance(node, MemberAssignmentNode):
            target_obj = self.execute(node.target, env)
            val = self.execute(node.value, env)
            if isinstance(target_obj, FractalCellInstance):
                target_obj.set_member(node.member, val)
                return val
            elif isinstance(target_obj, dict):
                target_obj[node.member] = val
                return val
            else:
                setattr(target_obj, node.member, val)
                return val

        if isinstance(node, IndexAssignmentNode):
            target_obj = self.execute(node.target, env)
            idx_val = self.execute(node.index, env)
            val = self.execute(node.value, env)
            target_obj[idx_val] = val
            return val

        if isinstance(node, IndexAccessNode):
            target_obj = self.execute(node.target, env)
            idx_val = self.execute(node.index, env)
            return target_obj[idx_val]

        if isinstance(node, MemberAccessNode):
            target_obj = self.execute(node.target, env)
            if isinstance(target_obj, FractalCellInstance):
                return target_obj.get_member(node.member)
            if isinstance(target_obj, dict):
                return target_obj[node.member]
            if hasattr(target_obj, node.member):
                return getattr(target_obj, node.member)
            raise AttributeError(f"Object {target_obj} has no attribute '{node.member}'")

        if isinstance(node, CallNode):
            callee = self.execute(node.callee, env)
            args = [self.execute(arg, env) for arg in node.args]
            return self._invoke_callable(callee, args)

        if isinstance(node, PipelineNode):
            # Left to right data piping
            left_val = self.execute(node.left, env)
            
            # Check if right is already a CallNode (e.g. filter(is_even))
            if isinstance(node.right, CallNode):
                callee = self.execute(node.right.callee, env)
                args = [left_val] + [self.execute(arg, env) for arg in node.right.args]
                return self._invoke_callable(callee, args)
            else:
                # Right is an expression evaluating to a function (e.g. print or square)
                right_callee = self.execute(node.right, env)
                return self._invoke_callable(right_callee, [left_val])

        if isinstance(node, BinaryOpNode):
            left_val = self.execute(node.left, env)
            right_val = self.execute(node.right, env)
            op = node.op
            if op == "+": return left_val + right_val
            if op == "-": return left_val - right_val
            if op == "*": return left_val * right_val
            if op == "/": return left_val / right_val
            if op == "%": return left_val % right_val
            if op == "^": return left_val ** right_val
            if op == "==": return left_val == right_val
            if op == "!=": return left_val != right_val
            if op == "<": return left_val < right_val
            if op == ">": return left_val > right_val
            if op == "<=": return left_val <= right_val
            if op == ">=": return left_val >= right_val
            if op == "and": return bool(left_val and right_val)
            if op == "or": return bool(left_val or right_val)
            raise ValueError(f"Unknown binary operator '{op}'")

        if isinstance(node, UnaryOpNode):
            val = self.execute(node.expr, env)
            if node.op == "-": return -val
            if node.op == "not": return not val
            raise ValueError(f"Unknown unary operator '{node.op}'")

        if isinstance(node, IfNode):
            cond_val = self.execute(node.condition, env)
            last = None
            if cond_val:
                for stmt in node.then_body:
                    last = self.execute(stmt, env)
            elif node.else_body:
                for stmt in node.else_body:
                    last = self.execute(stmt, env)
            return last

        if isinstance(node, ForNode):
            iterable = self.execute(node.iterable, env)
            last = None
            for item in iterable:
                loop_env = Environment(parent=env)
                loop_env.set(node.var_name, item)
                for stmt in node.body:
                    last = self.execute(stmt, loop_env)
            return last

        if isinstance(node, WhileNode):
            last = None
            while self.execute(node.condition, env):
                for stmt in node.body:
                    last = self.execute(stmt, env)
            return last

        if isinstance(node, UseNode):
            # Resolve module file
            resolved_path = os.path.abspath(node.module_path)
            if not os.path.exists(resolved_path):
                for suffix in (".sm", ".fc"):
                    if os.path.exists(resolved_path + suffix):
                        resolved_path += suffix
                        break
                else:
                    raise FileNotFoundError(f"Soma module not found: {node.module_path}")
            
            with open(resolved_path, "r", encoding="utf-8") as f:
                mod_src = f.read()

            from lexer import Lexer
            from parser import Parser
            mod_tokens = Lexer(mod_src).tokenize()
            mod_ast = Parser(mod_tokens).parse()
            mod_env = Environment(parent=self.global_env)
            for stmt in mod_ast.statements:
                self.execute(stmt, mod_env)

            module_name = node.alias or pathlib.Path(resolved_path).stem
            instance = FractalCellInstance(name=module_name, env=mod_env)
            env.set(module_name, instance)
            return instance

        if isinstance(node, SpawnNode):
            def run_worker():
                worker_env = Environment(parent=env)
                for stmt in node.body:
                    self.execute(stmt, worker_env)
            t = threading.Thread(target=run_worker, daemon=True)
            t.start()
            return t

        if isinstance(node, MatchNode):
            subject_val = self.execute(node.subject, env)
            for case in node.cases:
                match_env = Environment(parent=env)
                matched = False
                
                # Identifier in pattern: wildcard '_' or variable binding
                if isinstance(case.pattern, IdentifierNode):
                    if case.pattern.name == "_":
                        matched = True
                    elif case.pattern.name in env.bindings:
                        matched = (subject_val == env.get(case.pattern.name))
                    else:
                        match_env.set(case.pattern.name, subject_val)
                        matched = True
                else:
                    pat_val = self.execute(case.pattern, env)
                    matched = (subject_val == pat_val)

                if matched:
                    if case.guard:
                        guard_res = self.execute(case.guard, match_env)
                        if not guard_res:
                            continue
                    last = None
                    for stmt in case.body:
                        last = self.execute(stmt, match_env)
                    return last
            return None

        raise NotImplementedError(f"Execution not implemented for node: {type(node)}")

    def _invoke_callable(self, callee: Any, args: List[Any]) -> Any:
        if isinstance(callee, FractalCallableCell):
            return callee.call(args, self)
        elif callable(callee):
            return callee(*args)
        raise TypeError(f"'{callee}' is not callable")
