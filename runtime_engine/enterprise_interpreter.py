"""
Enterprise Production Execution Engine for Fractal.
Implements IExecutionStrategy, clean IoC, zero magic numbers,
strict error boundaries, call stack depth guards, and non-blocking telemetry.
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
    IndexAccessNode, IndexAssignmentNode, PipelineNode, CallNode,
    MemberAccessNode, BinaryOpNode, UnaryOpNode, LiteralNode, IdentifierNode,
    ListNode, MapNode, IfNode, ForNode, WhileNode, UseNode, MatchCaseNode,
    MatchNode, SpawnNode
)
from core.interfaces import IExecutionStrategy
from config.settings import SystemConfig, RuntimeConfig
from telemetry.logger import TelemetryLogger, MetricsCollector
from concurrency.circuit_breaker import CircuitBreaker

class RecursionLimitExceededException(RuntimeError):
    pass

class FractalRuntimeScope:
    __slots__ = ("bindings", "parent", "depth")

    def __init__(self, parent: Optional['FractalRuntimeScope'] = None, depth: int = 0):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent
        self.depth = depth

    def get(self, name: str) -> Any:
        curr = self
        while curr is not None:
            if name in curr.bindings:
                return curr.bindings[name]
            curr = curr.parent
        raise NameError(f"Undefined variable or cell '{name}' in active scope.")

    def set(self, name: str, value: Any) -> None:
        self.bindings[name] = value

    def assign(self, name: str, value: Any) -> None:
        curr = self
        while curr is not None:
            if name in curr.bindings:
                curr.bindings[name] = value
                return
            curr = curr.parent
        self.bindings[name] = value

class ProductionCellInstance:
    __slots__ = ("name", "scope")

    def __init__(self, name: str, scope: FractalRuntimeScope):
        self.name = name
        self.scope = scope

    def get_member(self, member: str) -> Any:
        if member in self.scope.bindings:
            return self.scope.bindings[member]
        raise AttributeError(f"Cell '{self.name}' has no member '{member}'")

    def set_member(self, member: str, value: Any) -> None:
        self.scope.bindings[member] = value

    def __repr__(self) -> str:
        return f"<Cell '{self.name}': {list(self.scope.bindings.keys())}>"

class ProductionCallableCell:
    __slots__ = ("name", "params", "body", "closure_scope")

    def __init__(self, name: str, params: List[str], body: List[ASTNode], closure_scope: FractalRuntimeScope):
        self.name = name
        self.params = params
        self.body = body
        self.closure_scope = closure_scope

    def __repr__(self) -> str:
        return f"<CallableCell '{self.name}({', '.join(self.params)})'>"

class EnterpriseInterpreterStrategy(IExecutionStrategy):
    __slots__ = ("_config", "_logger", "_metrics", "_circuit_breaker", "global_scope")

    def __init__(
        self,
        config: SystemConfig,
        logger: TelemetryLogger,
        metrics: MetricsCollector,
        circuit_breaker: CircuitBreaker
    ):
        self._config = config
        self._logger = logger
        self._metrics = metrics
        self._circuit_breaker = circuit_breaker
        self._sandbox = None
        self.global_scope = FractalRuntimeScope()
        self._init_builtins()

    def name(self) -> str:
        return "EnterpriseInterpreterStrategy"

    def _init_builtins(self) -> None:
        def _print(*args: Any) -> Any:
            formatted = [str(a) if not isinstance(a, bool) else ("true" if a else "false") for a in args]
            print(*formatted)
            return args[-1] if args else None

        def _sqrt(x: float) -> float: return math.sqrt(x)
        def _sin(x: float) -> float: return math.sin(x)
        def _cos(x: float) -> float: return math.cos(x)
        def _abs(x: float) -> float: return abs(x)
        def _len(x: Any) -> int: return len(x)
        def _range(*args: int) -> List[int]: return list(range(*args))
        def _str(x: Any) -> str: return str(x)
        def _int(x: Any) -> int: return int(x)
        def _float(x: Any) -> float: return float(x)
        def _type(x: Any) -> str: return type(x).__name__
        def _time() -> float: return time.time()
        def _perf() -> float: return time.perf_counter()
        def _sleep(s: float) -> None: time.sleep(s)

        def _call_user(fn: Any, args: List[Any]) -> Any:
            if isinstance(fn, ProductionCallableCell):
                return self._invoke(fn, args, self.global_scope)
            if callable(fn):
                return fn(*args)
            raise TypeError("Target must be callable")

        def _map(iterable: Any, fn: Any) -> List[Any]:
            return [_call_user(fn, [item]) for item in iterable]

        def _filter(iterable: Any, fn: Any) -> List[Any]:
            return [item for item in iterable if _call_user(fn, [item])]

        def _push(lst: List[Any], item: Any) -> List[Any]:
            lst.append(item)
            return lst
        
        class BoundedChannel:
            def __init__(self, capacity: int):
                self._q: queue.Queue[Any] = queue.Queue(maxsize=capacity)
            def send(self, val: Any) -> Any:
                self._q.put(val)
                return val
            def recv(self, timeout: Optional[float] = None) -> Any:
                return self._q.get(timeout=timeout)
            def empty(self) -> bool:
                return self._q.empty()
            def __repr__(self) -> str:
                return f"<Channel pending={self._q.qsize()}>"

        cap = self._config.runtime.max_channel_buffer_capacity
        def _channel() -> BoundedChannel:
            return BoundedChannel(capacity=cap)

        def _read_file(p: str) -> str:
            self._permit("READ_FILE", p)
            with open(p, "r", encoding="utf-8") as f:
                return f.read()

        def _write_file(p: str, content: Any) -> int:
            self._permit("WRITE_FILE", p)
            with open(p, "w", encoding="utf-8") as f:
                f.write(str(content))
            return len(str(content))

        self.global_scope.set("print", _print)
        self.global_scope.set("sqrt", _sqrt)
        self.global_scope.set("sin", _sin)
        self.global_scope.set("cos", _cos)
        self.global_scope.set("abs", _abs)
        self.global_scope.set("len", _len)
        self.global_scope.set("range", _range)
        self.global_scope.set("str", _str)
        self.global_scope.set("int", _int)
        self.global_scope.set("float", _float)
        self.global_scope.set("type", _type)
        self.global_scope.set("time", _time)
        self.global_scope.set("perf", _perf)
        self.global_scope.set("sleep", _sleep)
        self.global_scope.set("channel", _channel)
        self.global_scope.set("map", _map)
        self.global_scope.set("filter", _filter)
        self.global_scope.set("push", _push)
        self.global_scope.set("read_file", _read_file)
        self.global_scope.set("write_file", _write_file)

    def _permit(self, permission_name: str, resource: Optional[str] = None) -> None:
        if self._sandbox is None:
            return
        from security.sandbox import Permission
        self._sandbox.check_permission(Permission[permission_name], resource)

    def execute_ast(self, program: ProgramNode, context: Optional[Dict[str, Any]] = None) -> Any:
        return self._circuit_breaker.execute(lambda: self._execute_program_internal(program))

    def _execute_program_internal(self, program: ProgramNode) -> Any:
        t0 = time.perf_counter()
        result = None
        for stmt in program.statements:
            result = self.execute_node(stmt, self.global_scope)
        duration_ms = (time.perf_counter() - t0) * 1000
        self._metrics.record_timing("program_execution_ms", duration_ms)
        self._logger.debug("Program execution completed", duration_ms=duration_ms)
        return result

    def execute_node(self, node: ASTNode, scope: FractalRuntimeScope) -> Any:
        if scope.depth > self._config.runtime.max_recursion_depth:
            raise RecursionLimitExceededException(
                f"Call stack recursion limit ({self._config.runtime.max_recursion_depth}) exceeded."
            )

        if isinstance(node, LiteralNode):
            return node.value

        if isinstance(node, IdentifierNode):
            return scope.get(node.name)

        if isinstance(node, ListNode):
            return [self.execute_node(elem, scope) for elem in node.elements]

        if isinstance(node, MapNode):
            return {self.execute_node(k, scope): self.execute_node(v, scope) for k, v in node.pairs}

        if isinstance(node, CellDefNode):
            if node.params is not None:
                callable_cell = ProductionCallableCell(
                    name=node.name,
                    params=node.params,
                    body=node.body,
                    closure_scope=scope
                )
                scope.set(node.name, callable_cell)
                return callable_cell
            else:
                if len(node.body) == 1 and not isinstance(node.body[0], CellDefNode):
                    val = self.execute_node(node.body[0], scope)
                    scope.set(node.name, val)
                    return val
                else:
                    child_scope = FractalRuntimeScope(parent=scope, depth=scope.depth + 1)
                    last_val = None
                    for child_stmt in node.body:
                        last_val = self.execute_node(child_stmt, child_scope)
                    instance = ProductionCellInstance(name=node.name, scope=child_scope)
                    scope.set(node.name, instance)
                    return instance

        if isinstance(node, AssignmentNode):
            val = self.execute_node(node.value, scope)
            scope.assign(node.target, val)
            return val

        if isinstance(node, MemberAssignmentNode):
            target = self.execute_node(node.target, scope)
            val = self.execute_node(node.value, scope)
            if isinstance(target, ProductionCellInstance):
                target.set_member(node.member, val)
            elif isinstance(target, dict):
                target[node.member] = val
            else:
                setattr(target, node.member, val)
            return val

        if isinstance(node, IndexAssignmentNode):
            target = self.execute_node(node.target, scope)
            idx = self.execute_node(node.index, scope)
            val = self.execute_node(node.value, scope)
            target[idx] = val
            return val

        if isinstance(node, IndexAccessNode):
            target = self.execute_node(node.target, scope)
            idx = self.execute_node(node.index, scope)
            return target[idx]

        if isinstance(node, MemberAccessNode):
            target = self.execute_node(node.target, scope)
            if isinstance(target, ProductionCellInstance):
                return target.get_member(node.member)
            if isinstance(target, dict):
                return target[node.member]
            if hasattr(target, node.member):
                return getattr(target, node.member)
            raise AttributeError(f"Object {target} has no member '{node.member}'")

        if isinstance(node, CallNode):
            callee = self.execute_node(node.callee, scope)
            args = [self.execute_node(arg, scope) for arg in node.args]
            return self._invoke(callee, args, scope)

        if isinstance(node, PipelineNode):
            left_val = self.execute_node(node.left, scope)
            if isinstance(node.right, CallNode):
                callee = self.execute_node(node.right.callee, scope)
                args = [left_val] + [self.execute_node(a, scope) for a in node.right.args]
                return self._invoke(callee, args, scope)
            else:
                right_callee = self.execute_node(node.right, scope)
                return self._invoke(right_callee, [left_val], scope)

        if isinstance(node, BinaryOpNode):
            l = self.execute_node(node.left, scope)
            r = self.execute_node(node.right, scope)
            op = node.op
            if op == "+": return l + r
            if op == "-": return l - r
            if op == "*": return l * r
            if op == "/": return l / r
            if op == "%": return l % r
            if op == "^": return l ** r
            if op == "==": return l == r
            if op == "!=": return l != r
            if op == "<": return l < r
            if op == ">": return l > r
            if op == "<=": return l <= r
            if op == ">=": return l >= r
            if op == "and": return bool(l and r)
            if op == "or": return bool(l or r)
            raise ValueError(f"Unknown binary operator '{op}'")

        if isinstance(node, UnaryOpNode):
            v = self.execute_node(node.expr, scope)
            if node.op == "-": return -v
            if node.op == "not": return not v
            raise ValueError(f"Unknown unary operator '{node.op}'")

        if isinstance(node, IfNode):
            cond = self.execute_node(node.condition, scope)
            last = None
            if cond:
                for stmt in node.then_body:
                    last = self.execute_node(stmt, scope)
            elif node.else_body:
                for stmt in node.else_body:
                    last = self.execute_node(stmt, scope)
            return last

        if isinstance(node, ForNode):
            iterable = self.execute_node(node.iterable, scope)
            last = None
            for item in iterable:
                loop_scope = FractalRuntimeScope(parent=scope, depth=scope.depth + 1)
                loop_scope.set(node.var_name, item)
                for stmt in node.body:
                    last = self.execute_node(stmt, loop_scope)
            return last

        if isinstance(node, WhileNode):
            last = None
            while self.execute_node(node.condition, scope):
                for stmt in node.body:
                    last = self.execute_node(stmt, scope)
            return last

        if isinstance(node, UseNode):
            resolved_path = os.path.abspath(node.module_path)
            if not os.path.exists(resolved_path):
                for suffix in (".sm", ".fc"):
                    if os.path.exists(resolved_path + suffix):
                        resolved_path += suffix
                        break
                else:
                    raise FileNotFoundError(f"Soma module not found: {node.module_path}")
            self._permit("READ_FILE", resolved_path)
            
            with open(resolved_path, "r", encoding="utf-8") as f:
                src = f.read()

            from lexer import Lexer
            from parser import Parser
            tokens = Lexer(src).tokenize()
            mod_ast = Parser(tokens).parse()
            mod_scope = FractalRuntimeScope(parent=self.global_scope, depth=0)
            for stmt in mod_ast.statements:
                self.execute_node(stmt, mod_scope)

            mod_name = node.alias or pathlib.Path(resolved_path).stem
            instance = ProductionCellInstance(name=mod_name, scope=mod_scope)
            scope.set(mod_name, instance)
            return instance

        if isinstance(node, SpawnNode):
            self._permit("CONCURRENCY_SPAWN")
            def _async_worker():
                worker_scope = FractalRuntimeScope(parent=scope, depth=scope.depth + 1)
                for stmt in node.body:
                    self.execute_node(stmt, worker_scope)
            t = threading.Thread(target=_async_worker, daemon=True)
            t.start()
            return t

        if isinstance(node, MatchNode):
            subj = self.execute_node(node.subject, scope)
            for case in node.cases:
                match_scope = FractalRuntimeScope(parent=scope, depth=scope.depth + 1)
                matched = False
                if isinstance(case.pattern, IdentifierNode):
                    if case.pattern.name == "_":
                        matched = True
                    elif case.pattern.name in scope.bindings:
                        matched = (subj == scope.get(case.pattern.name))
                    else:
                        match_scope.set(case.pattern.name, subj)
                        matched = True
                else:
                    pat_val = self.execute_node(case.pattern, scope)
                    matched = (subj == pat_val)

                if matched:
                    if case.guard:
                        guard_val = self.execute_node(case.guard, match_scope)
                        if not guard_val:
                            continue
                    last = None
                    for stmt in case.body:
                        last = self.execute_node(stmt, match_scope)
                    return last
            return None

        raise NotImplementedError(f"Execution node {type(node)} has no registered handler.")

    def _invoke(self, callee: Any, args: List[Any], calling_scope: FractalRuntimeScope) -> Any:
        if isinstance(callee, ProductionCallableCell):
            if len(args) != len(callee.params):
                raise TypeError(
                    f"Cell '{callee.name}' expects {len(callee.params)} args ({callee.params}), received {len(args)}"
                )
            call_scope = FractalRuntimeScope(
                parent=callee.closure_scope,
                depth=calling_scope.depth + 1
            )
            for p_name, arg_val in zip(callee.params, args):
                call_scope.set(p_name, arg_val)

            last_val = None
            has_sub_cells = False
            for stmt in callee.body:
                if isinstance(stmt, CellDefNode):
                    has_sub_cells = True
                last_val = self.execute_node(stmt, call_scope)

            if has_sub_cells and (not callee.body or isinstance(callee.body[-1], CellDefNode)):
                return ProductionCellInstance(name=callee.name, scope=call_scope)
            return last_val

        elif callable(callee):
            return callee(*args)

        raise TypeError(f"Target '{callee}' is not invocable as a Cell.")
