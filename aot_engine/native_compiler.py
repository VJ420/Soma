"""Soma native compiler.

One Soma program, concrete machine types. The lowering is the product engine:

- monomorphized int64 and double cells
- contiguous vectors
- bit-packed boolean arrays
- object cells as arena-allocated structs
- counted while-loops rewritten as for-loops
- pipelines lowered to direct calls
- match lowered to comparisons
- spawn joined by RAII so the task finishes with the cell that started it
"""

from __future__ import annotations

from lexer import Lexer
from parser import Parser
from ast_nodes import (
    ASTNode,
    AssignmentNode,
    BinaryOpNode,
    CallNode,
    CellDefNode,
    ForNode,
    IdentifierNode,
    IfNode,
    IndexAccessNode,
    IndexAssignmentNode,
    ListNode,
    LiteralNode,
    MatchNode,
    MemberAccessNode,
    MemberAssignmentNode,
    PipelineNode,
    ProgramNode,
    SpawnNode,
    UnaryOpNode,
    UseNode,
    WhileNode,
)


class NativeCompileError(Exception):
    pass


BOTTOM = ("bottom",)
I64 = ("i64",)
F64 = ("f64",)
BOOL = ("bool",)
STR = ("str",)
BITS = ("bits",)
ANY = ("any",)


def join(left, right):
    if left == BOTTOM:
        return right
    if right == BOTTOM:
        return left
    if left == right:
        return left
    if left == ANY or right == ANY:
        return ANY
    if {left[0], right[0]} <= {"i64", "f64"}:
        return F64
    if BITS in (left, right) and {left[0], right[0]} <= {"bits", "bool", "vec", "i64"}:
        return BITS
    if left == BOOL and right[0] == "vec":
        return BITS
    if right == BOOL and left[0] == "vec":
        return BITS
    if left[0] == "vec" and right[0] == "vec":
        element = join(left[1], right[1])
        if element == BOOL:
            return BITS
        if element == ANY:
            return ANY
        return ("vec", element)
    if left[0] == "obj" and right[0] == "obj" and left[1] == right[1]:
        return left
    return ANY


class NativeCompiler:
    def __init__(self):
        self.types: dict = {}
        self.functions: dict[str, CellDefNode] = {}
        self.objects: dict[str, CellDefNode] = {}
        self.methods: dict[str, dict[str, CellDefNode]] = {}
        self.main_stmts: list[ASTNode] = []
        self.return_types: dict[str, tuple] = {}
        self._recording = True

    def compile_source(self, source: str) -> str:
        return self.compile_program(Parser(Lexer(source).tokenize()).parse())

    def compile_program(self, program: ProgramNode) -> str:
        self._classify(program)
        self._infer()
        return self._emit()

    def _classify(self, program: ProgramNode) -> None:
        for stmt in program.statements:
            if isinstance(stmt, CellDefNode) and stmt.params is not None and self._is_object(stmt):
                self.objects[stmt.name] = stmt
                self.methods[stmt.name] = {
                    child.name: child
                    for child in stmt.body
                    if isinstance(child, CellDefNode) and child.params is not None
                }
                self.return_types[stmt.name] = ("obj", stmt.name)
            elif isinstance(stmt, CellDefNode) and stmt.params is not None:
                self.functions[stmt.name] = stmt
            elif isinstance(stmt, CellDefNode) and stmt.params is None and self._is_value(stmt):
                self.main_stmts.append(AssignmentNode(stmt.name, stmt.body[0]))
            else:
                self.main_stmts.append(stmt)

    def _is_object(self, cell: CellDefNode) -> bool:
        return any(isinstance(child, CellDefNode) and child.params is not None for child in cell.body)

    def _is_value(self, cell: CellDefNode) -> bool:
        return len(cell.body) == 1 and not isinstance(cell.body[0], CellDefNode)

    def _fields(self, obj: str) -> list[str]:
        cell = self.objects[obj]
        fields = list(cell.params or [])
        for child in cell.body:
            if isinstance(child, AssignmentNode) and child.target not in fields:
                fields.append(child.target)
        return fields

    def _widen(self, key, typ) -> None:
        if not self._recording:
            return
        current = self.types.get(key, BOTTOM)
        merged = join(current, typ)
        self.types[key] = merged

    def _get(self, key):
        return self.types.get(key, BOTTOM)

    def _lookup(self, scope: str, name: str):
        local = self._get((scope, name))
        if local != BOTTOM:
            return local
        obj = scope.split(".", 1)[0] if "." in scope else None
        if obj in self.objects and name in self._fields(obj):
            return self._get(("field", obj, name))
        if scope != "main":
            outer = self._get(("main", name))
            if outer != BOTTOM:
                return outer
        return BOTTOM

    def _infer(self) -> None:
        for _ in range(32):
            before = dict(self.types)
            before_returns = dict(self.return_types)
            for name, cell in self.functions.items():
                self._infer_body(name, cell, None)
            for name, cell in self.objects.items():
                self._infer_constructor(name, cell)
                for method_name, method in self.methods[name].items():
                    self._infer_body(f"{name}.{method_name}", method, name)
            self._infer_block("main", [self._normalize(stmt) for stmt in self.main_stmts], None)
            if self.types == before and self.return_types == before_returns:
                break

    def _normalize(self, stmt: ASTNode) -> ASTNode:
        if isinstance(stmt, CellDefNode) and self._is_value(stmt):
            return AssignmentNode(stmt.name, stmt.body[0])
        return stmt

    def _infer_constructor(self, name: str, cell: CellDefNode) -> None:
        scope = f"{name}.__new__"
        for field in self._fields(name):
            if field in (cell.params or []):
                self._widen(("field", name, field), self._get((name, field)))
        for child in cell.body:
            if isinstance(child, CellDefNode):
                continue
            stmt = self._normalize(child)
            if isinstance(stmt, AssignmentNode):
                typ = self._expr_type(stmt.value, scope, name)
                self._widen(("field", name, stmt.target), typ)
                self._widen((scope, stmt.target), typ)
            else:
                self._infer_stmt(stmt, scope, name)

    def _infer_body(self, scope: str, cell: CellDefNode, obj: str | None) -> None:
        for param in cell.params or []:
            self._widen((scope, param), self._get((scope, param)))
        tail = self._infer_block(scope, cell.body, obj)
        self.return_types[scope] = join(self.return_types.get(scope, BOTTOM), tail)

    def _infer_block(self, scope: str, stmts: list[ASTNode], obj: str | None):
        if not stmts:
            return BOTTOM
        for stmt in stmts[:-1]:
            self._infer_stmt(self._normalize(stmt), scope, obj)
        last = self._normalize(stmts[-1])
        if isinstance(last, IfNode):
            self._infer_stmt(last, scope, obj)
            then_t = self._infer_block(scope, last.then_body, obj)
            else_t = self._infer_block(scope, last.else_body, obj) if last.else_body else BOTTOM
            return join(then_t, else_t) if last.else_body else then_t
        if isinstance(last, MatchNode):
            return self._infer_match(last, scope, obj)
        if isinstance(last, (AssignmentNode, WhileNode, ForNode, IndexAssignmentNode, MemberAssignmentNode, SpawnNode, CellDefNode)):
            self._infer_stmt(last, scope, obj)
            return BOTTOM
        return self._expr_type(last, scope, obj)

    def _infer_match(self, node: MatchNode, scope: str, obj: str | None):
        subject = self._expr_type(node.subject, scope, obj)
        result = BOTTOM
        for case in node.cases:
            if isinstance(case.pattern, IdentifierNode) and case.pattern.name != "_":
                self._widen((scope, case.pattern.name), subject)
            if case.guard is not None:
                self._expr_type(case.guard, scope, obj)
            result = join(result, self._infer_block(scope, case.body, obj))
        return result

    def _infer_stmt(self, stmt: ASTNode, scope: str, obj: str | None) -> None:
        stmt = self._normalize(stmt)
        if isinstance(stmt, AssignmentNode):
            typ = self._expr_type(stmt.value, scope, obj)
            if obj and stmt.target in self._fields(obj):
                self._widen(("field", obj, stmt.target), typ)
            else:
                self._widen((scope, stmt.target), typ)
            return
        if isinstance(stmt, IndexAssignmentNode):
            self._expr_type(stmt.target, scope, obj)
            self._expr_type(stmt.index, scope, obj)
            value = self._expr_type(stmt.value, scope, obj)
            if isinstance(stmt.target, IdentifierNode):
                self._note_index(scope, stmt.target.name, value)
            return
        if isinstance(stmt, MemberAssignmentNode):
            self._expr_type(stmt.value, scope, obj)
            return
        if isinstance(stmt, IfNode):
            self._expr_type(stmt.condition, scope, obj)
            for child in stmt.then_body:
                self._infer_stmt(child, scope, obj)
            for child in stmt.else_body or []:
                self._infer_stmt(child, scope, obj)
            return
        if isinstance(stmt, WhileNode):
            self._expr_type(stmt.condition, scope, obj)
            for child in stmt.body:
                self._infer_stmt(child, scope, obj)
            return
        if isinstance(stmt, ForNode):
            iterable = self._expr_type(stmt.iterable, scope, obj)
            element = iterable[1] if iterable[0] == "vec" else I64
            self._widen((scope, stmt.var_name), element)
            for child in stmt.body:
                self._infer_stmt(child, scope, obj)
            return
        if isinstance(stmt, MatchNode):
            self._infer_match(stmt, scope, obj)
            return
        if isinstance(stmt, SpawnNode):
            for child in stmt.body:
                self._infer_stmt(child, scope, obj)
            return
        if isinstance(stmt, (CellDefNode, UseNode)):
            raise NativeCompileError(f"{type(stmt).__name__} is not lowered in this scope")
        self._expr_type(stmt, scope, obj)

    def _note_index(self, scope: str, name: str, element) -> None:
        if element == BOOL:
            self._widen((scope, name), BITS)
            return
        current = self._lookup(scope, name)
        if current == BITS or current == BOTTOM and element == BOOL:
            self._widen((scope, name), BITS)
            return
        if current[0] == "vec":
            self._widen((scope, name), ("vec", join(current[1], element)))
            return
        if current == BOTTOM:
            self._widen((scope, name), ("vec", element if element != BOTTOM else I64))

    def _expr_type(self, node: ASTNode, scope: str, obj: str | None):
        if isinstance(node, LiteralNode):
            if isinstance(node.value, bool):
                return BOOL
            if isinstance(node.value, str):
                return STR
            if node.value is None:
                return BOTTOM
            if isinstance(node.value, float):
                return F64
            return I64
        if isinstance(node, IdentifierNode):
            return self._lookup(scope, node.name)
        if isinstance(node, ListNode):
            element = BOTTOM
            for item in node.elements:
                element = join(element, self._expr_type(item, scope, obj))
            return ("vec", I64 if element == BOTTOM else element)
        if isinstance(node, UnaryOpNode):
            inner = self._expr_type(node.expr, scope, obj)
            if node.op == "not":
                return BOOL
            return inner if inner != BOTTOM else I64
        if isinstance(node, BinaryOpNode):
            left = self._expr_type(node.left, scope, obj)
            right = self._expr_type(node.right, scope, obj)
            if node.op in ("and", "or", "==", "!=", "<", ">", "<=", ">="):
                return BOOL
            if node.op == "+" and (left == STR or right == STR):
                return STR
            if node.op == "/":
                return F64
            if node.op == "^":
                return F64
            return join(left if left != BOTTOM else I64, right if right != BOTTOM else I64)
        if isinstance(node, PipelineNode):
            self._expr_type(node.left, scope, obj)
            if isinstance(node.right, CallNode):
                return self._call_type(node.right.callee, [node.left, *node.right.args], scope, obj)
            return self._call_type(node.right, [node.left], scope, obj)
        if isinstance(node, IndexAccessNode):
            target = self._expr_type(node.target, scope, obj)
            self._expr_type(node.index, scope, obj)
            if target == BITS:
                return BOOL
            if target[0] == "vec":
                return target[1]
            return BOTTOM
        if isinstance(node, MemberAccessNode):
            target = self._expr_type(node.target, scope, obj)
            if target[0] == "obj" and node.member in self._fields(target[1]):
                return self._get(("field", target[1], node.member))
            return BOTTOM
        if isinstance(node, CallNode):
            return self._call_type(node.callee, node.args, scope, obj)
        if isinstance(node, MatchNode):
            return self._infer_match(node, scope, obj)
        if isinstance(node, IfNode):
            self._expr_type(node.condition, scope, obj)
            then_t = self._infer_block(scope, node.then_body, obj)
            else_t = self._infer_block(scope, node.else_body, obj) if node.else_body else BOTTOM
            return join(then_t, else_t) if node.else_body else then_t
        raise NativeCompileError(f"{type(node).__name__} has no native type")

    def _call_type(self, callee: ASTNode, args: list[ASTNode], scope: str, obj: str | None):
        arg_types = [self._expr_type(arg, scope, obj) for arg in args]
        if isinstance(callee, IdentifierNode):
            name = callee.name
            if name == "range":
                return ("vec", I64)
            if name in ("sqrt", "sin", "cos", "perf", "float", "time"):
                return F64
            if name in ("str",):
                return STR
            if name in ("len", "int", "abs"):
                if name == "abs" and arg_types and arg_types[0] == F64:
                    return F64
                return I64
            if name in self.objects:
                for param, typ in zip(self.objects[name].params or [], arg_types):
                    self._widen((name, param), typ)
                    self._widen(("field", name, param), typ)
                return ("obj", name)
            if name in self.functions:
                for param, typ in zip(self.functions[name].params or [], arg_types):
                    self._widen((name, param), typ)
                return self.return_types.get(name, BOTTOM)
            if name == "print":
                return BOTTOM
            return BOTTOM
        if isinstance(callee, MemberAccessNode):
            target = self._expr_type(callee.target, scope, obj)
            if target[0] != "obj":
                return BOTTOM
            method = self.methods.get(target[1], {}).get(callee.member)
            if method is None:
                return BOTTOM
            method_scope = f"{target[1]}.{callee.member}"
            for param, typ in zip(method.params or [], arg_types):
                self._widen((method_scope, param), typ)
            return self.return_types.get(method_scope, BOTTOM)
        raise NativeCompileError("unsupported call shape")

    def _emit(self) -> str:
        self._recording = False
        chunks = [self._preamble()]
        if self.objects:
            chunks.append("\n".join(f"struct {name};" for name in self.objects))
        for name in self.functions:
            chunks.append(self._prototype(name, self.functions[name], name))
        for name in self.objects:
            chunks.append(self._prototype(name, self.objects[name], name, pointer=True))
            for method_name, method in self.methods[name].items():
                scope = f"{name}.{method_name}"
                chunks.append(self._prototype(method_name, method, scope, owner=name))
        for name in self.objects:
            chunks.append(self._emit_struct(name))
            chunks.append(self._emit_factory(name))
        for name, cell in self.functions.items():
            chunks.append(self._emit_function(name, cell, name, None))
        chunks.append(self._emit_main())
        return "\n\n".join(chunks) + "\n"

    def _preamble(self) -> str:
        return """// Soma native lowering. Generated. Do not edit.
#include <chrono>
#include <cmath>
#include <cstdint>
#include <deque>
#include <future>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

struct SomaBits {
  int64_t length = 0;
  std::vector<uint64_t> words;
  SomaBits() = default;
  explicit SomaBits(int64_t n)
      : length(n < 0 ? 0 : n),
        words(static_cast<size_t>((n < 0 ? 0 : n) + 63) / 64) {}
  bool get(int64_t index) const {
    return (words[static_cast<size_t>(index >> 6)] >> (index & 63)) & 1ULL;
  }
  void set(int64_t index, bool value) {
    auto& word = words[static_cast<size_t>(index >> 6)];
    const uint64_t mask = 1ULL << (index & 63);
    if (value) word |= mask;
    else word &= ~mask;
  }
};

struct SomaJoin {
  std::vector<std::future<void>> jobs;
  ~SomaJoin() {
    for (auto& job : jobs) if (job.valid()) job.wait();
  }
};

template <typename T>
struct SomaArena {
  std::deque<T> items;
  T* alloc() {
    items.emplace_back();
    return &items.back();
  }
};

inline std::string soma_str(const std::string& value) { return value; }
inline std::string soma_str(int64_t value) { return std::to_string(value); }
inline std::string soma_str(bool value) { return value ? "true" : "false"; }
inline std::string soma_str(double value) {
  std::ostringstream out;
  out.setf(std::ios::fmtflags(0), std::ios::floatfield);
  out << std::setprecision(17) << value;
  return out.str();
}

inline void print() { std::cout << '\\n'; }
template <typename T, typename... Rest>
inline void print(T&& first, Rest&&... rest) {
  std::cout << std::forward<T>(first);
  if constexpr (sizeof...(Rest) > 0) std::cout << ' ';
  print(std::forward<Rest>(rest)...);
}

inline double perf() {
  return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline double soma_sqrt(double value) { return std::sqrt(value); }
inline double soma_sin(double value) { return std::sin(value); }
inline double soma_cos(double value) { return std::cos(value); }
inline int64_t soma_abs_i(int64_t value) { return value < 0 ? -value : value; }
inline double soma_abs_f(double value) { return value < 0 ? -value : value; }
"""

    def _cpp_type(self, typ, ref: bool = False) -> str:
        if typ == I64:
            return "int64_t"
        if typ == F64:
            return "double"
        if typ == BOOL:
            return "bool"
        if typ == STR:
            return "const std::string&" if ref else "std::string"
        if typ == BITS:
            return "SomaBits&" if ref else "SomaBits"
        if typ[0] == "vec":
            inner = "double" if typ[1] == F64 else "int64_t"
            base = f"std::vector<{inner}>"
            return f"{base}&" if ref else base
        if typ[0] == "obj":
            return f"{typ[1]}*"
        if typ == BOTTOM:
            return "int64_t"
        raise NativeCompileError(f"no C++ type for {typ}")

    def _require(self, typ, what: str):
        if typ == ANY or typ == BOTTOM:
            raise NativeCompileError(f"could not specialize {what} ({typ[0]})")
        return typ

    def _prototype(self, name: str, cell: CellDefNode, scope: str, pointer: bool = False, owner: str | None = None) -> str:
        ret = self.return_types.get(scope, BOTTOM)
        if pointer:
            ret_s = f"{name}*"
        elif ret == BOTTOM:
            ret_s = "void"
        else:
            ret_s = self._cpp_type(self._require(ret, name))
        params = []
        for param in cell.params or []:
            if owner:
                typ = self._require(self._get((scope, param)), f"{scope}::{param}")
            elif pointer:
                typ = self._require(self._get(("field", name, param)) if self._get(("field", name, param)) != BOTTOM else self._get((name, param)), f"{name}.{param}")
            else:
                typ = self._require(self._get((scope, param)), f"{name}.{param}")
            params.append(f"{self._cpp_type(typ, ref=True)} {param}")
        joined = ", ".join(params)
        if owner:
            return f"// method {owner}::{name}({joined}) -> {ret_s}"
        target = f"{name}_call" if pointer else name
        return f"static {ret_s} {target}({joined});"

    def _emit_struct(self, name: str) -> str:
        lines = [f"struct {name} {{"]
        for field in self._fields(name):
            typ = self._require(self._get(("field", name, field)), f"field {name}.{field}")
            lines.append(f"  {self._cpp_type(typ)} {field}{{}};" if typ != STR else f"  std::string {field};")
            if typ[0] == "obj":
                lines[-1] = f"  {typ[1]}* {field} = nullptr;"
            elif typ == I64:
                lines[-1] = f"  int64_t {field} = 0;"
            elif typ == F64:
                lines[-1] = f"  double {field} = 0;"
            elif typ == BOOL:
                lines[-1] = f"  bool {field} = false;"
            elif typ == STR:
                lines[-1] = f"  std::string {field};"
        lines.append(f"}};")
        lines.append(f"SomaArena<{name}> arena_{name};")
        method_lines = []
        for method_name, method in self.methods[name].items():
            scope = f"{name}.{method_name}"
            ret = self.return_types.get(scope, BOTTOM)
            ret_s = "void" if ret == BOTTOM else self._cpp_type(self._require(ret, scope))
            params = []
            for param in method.params or []:
                typ = self._require(self._get((scope, param)), f"{scope}.{param}")
                params.append(f"{self._cpp_type(typ, ref=True)} {param}")
            body = self._emit_block(method.body, scope, name, tail_returns=ret != BOTTOM, indent=2, declare=True)
            method_lines.append(f"  {ret_s} {method_name}({', '.join(params)}) {{\n{body}\n  }}")
        # Methods must live inside the struct. Rebuild with methods included.
        struct_lines = [f"struct {name} {{"]
        struct_lines.extend(lines[1:-2])
        struct_lines.extend(method_lines)
        struct_lines.append("};")
        struct_lines.append(f"SomaArena<{name}> arena_{name};")
        return "\n".join(struct_lines)

    def _emit_factory(self, name: str) -> str:
        cell = self.objects[name]
        params = []
        inits = []
        for param in cell.params or []:
            typ = self._require(self._get(("field", name, param)), f"{name}.{param}")
            params.append(f"{self._cpp_type(typ, ref=True)} {param}")
            inits.append(f"  soma_self->{param} = {param};")
        body_stmts = [child for child in cell.body if not isinstance(child, CellDefNode)]
        body = self._emit_block(body_stmts, f"{name}.__new__", name, tail_returns=False, indent=1, declare=True)
        joined = "\n".join(inits + ([body] if body else []))
        return (
            f"static {name}* {name}_call({', '.join(params)}) {{\n"
            f"  {name}* soma_self = arena_{name}.alloc();\n"
            f"{joined}\n"
            f"  return soma_self;\n}}"
        )

    def _emit_function(self, name: str, cell: CellDefNode, scope: str, obj: str | None) -> str:
        ret = self.return_types.get(scope, BOTTOM)
        ret_s = "void" if ret == BOTTOM else self._cpp_type(self._require(ret, name))
        params = []
        for param in cell.params or []:
            typ = self._require(self._get((scope, param)), f"{name}.{param}")
            params.append(f"{self._cpp_type(typ, ref=True)} {param}")
        body = self._emit_block(cell.body, scope, obj, tail_returns=ret != BOTTOM, indent=1, declare=True)
        return f"static {ret_s} {name}({', '.join(params)}) {{\n{body}\n}}"

    def _emit_main(self) -> str:
        body = self._emit_block(self.main_stmts, "main", None, tail_returns=False, indent=1, declare=True)
        return f"int main() {{\n  std::ios_base::sync_with_stdio(false);\n  std::cin.tie(nullptr);\n{body}\n  return 0;\n}}"

    def _emit_block(self, stmts: list[ASTNode], scope: str, obj: str | None, tail_returns: bool, indent: int, declare: bool = False) -> str:
        locals_ = self._locals(stmts, scope, obj) if declare else []
        lines = []
        pad = "  " * indent
        for name, typ in locals_:
            if typ[0] == "obj":
                lines.append(f"{pad}{typ[1]}* {name} = nullptr;")
            elif typ == F64:
                lines.append(f"{pad}double {name} = 0;")
            elif typ == BOOL:
                lines.append(f"{pad}bool {name} = false;")
            elif typ == STR:
                lines.append(f"{pad}std::string {name};")
            elif typ == BITS:
                lines.append(f"{pad}SomaBits {name};")
            elif typ[0] == "vec":
                lines.append(f"{pad}{self._cpp_type(typ)} {name};")
            else:
                lines.append(f"{pad}int64_t {name} = 0;")
        if declare:
            lines.append(f"{pad}SomaJoin soma_join;")
        fused = self._fuse(stmts)
        for index, item in enumerate(fused):
            last = index == len(fused) - 1
            if item[0] == "for":
                lines.append(self._emit_for(item, scope, obj, indent))
            elif item[0] == "swap":
                lines.append(f"{pad}std::swap({item[1]}, {item[2]});")
            else:
                lines.append(self._emit_stmt(item[1], scope, obj, tail_returns=tail_returns and last, indent=indent))
        return "\n".join(lines)

    def _locals(self, stmts: list[ASTNode], scope: str, obj: str | None) -> list[tuple[str, tuple]]:
        names: list[str] = []

        def add(name: str) -> None:
            if name not in names:
                names.append(name)

        def walk(nodes: list[ASTNode]) -> None:
            for node in nodes:
                node = self._normalize(node)
                if isinstance(node, AssignmentNode):
                    if not (obj and node.target in self._fields(obj)):
                        add(node.target)
                elif isinstance(node, IfNode):
                    walk(node.then_body)
                    if node.else_body:
                        walk(node.else_body)
                elif isinstance(node, (WhileNode, SpawnNode)):
                    walk(node.body)
                elif isinstance(node, MatchNode):
                    for case in node.cases:
                        walk(case.body)
                elif isinstance(node, ForNode):
                    walk(node.body)

        walk(stmts)
        params = set()
        if scope in self.functions:
            params.update(self.functions[scope].params or [])
        if obj and scope.startswith(obj + "."):
            method_name = scope.split(".", 1)[1]
            method = self.methods.get(obj, {}).get(method_name)
            if method:
                params.update(method.params or [])
            params.update(self._fields(obj))
        result = []
        for name in names:
            if name in params:
                continue
            typ = self._lookup(scope, name)
            if typ == BOTTOM or typ == ANY:
                raise NativeCompileError(f"could not specialize local {scope}.{name}")
            result.append((name, typ))
        return result

    def _fuse(self, stmts: list[ASTNode]) -> list:
        items = []
        index = 0
        normalized = [self._normalize(stmt) for stmt in stmts]
        while index < len(normalized):
            if index + 2 < len(normalized) and self._is_rotation(normalized[index:index + 3]):
                moved = normalized[index + 1]
                items.append(("swap", moved.target, moved.value.name))
                index += 3
            elif index + 1 < len(normalized) and self._can_fuse(normalized[index], normalized[index + 1]):
                items.append(("for", normalized[index], normalized[index + 1]))
                index += 2
            else:
                items.append(("stmt", normalized[index]))
                index += 1
        return items

    def _can_fuse(self, init: ASTNode, loop: ASTNode) -> bool:
        if not isinstance(init, AssignmentNode) or not isinstance(loop, WhileNode) or not loop.body:
            return False
        cond = loop.condition
        if not isinstance(cond, BinaryOpNode) or cond.op not in ("<", "<=", ">", ">="):
            return False
        if not isinstance(cond.left, IdentifierNode) or cond.left.name != init.target:
            return False
        step = loop.body[-1]
        if not isinstance(step, AssignmentNode) or step.target != init.target:
            return False
        value = step.value
        if not isinstance(value, BinaryOpNode) or value.op not in ("+", "-"):
            return False
        if not isinstance(value.left, IdentifierNode) or value.left.name != init.target:
            return False
        return not self._assigns(loop.body[:-1], init.target)

    def _is_rotation(self, stmts: list[ASTNode]) -> bool:
        first, second, third = stmts
        nodes = (first, second, third)
        if not all(isinstance(stmt, AssignmentNode) and isinstance(stmt.value, IdentifierNode) for stmt in nodes):
            return False
        return (
            first.value.name == second.target
            and second.value.name == third.target
            and third.value.name == first.target
            and first.target != second.target
        )

    def _assigns(self, stmts: list[ASTNode], name: str) -> bool:
        for stmt in stmts:
            stmt = self._normalize(stmt)
            if isinstance(stmt, AssignmentNode) and stmt.target == name:
                return True
            if isinstance(stmt, IfNode):
                if self._assigns(stmt.then_body, name) or self._assigns(stmt.else_body or [], name):
                    return True
            if isinstance(stmt, WhileNode) and self._assigns(stmt.body, name):
                return True
        return False

    def _emit_for(self, item, scope: str, obj: str | None, indent: int) -> str:
        _kind, init, loop = item
        step = loop.body[-1].value
        op = "+=" if step.op == "+" else "-="
        pad = "  " * indent
        body = self._emit_block(loop.body[:-1], scope, obj, tail_returns=False, indent=indent + 1, declare=False)
        return (
            f"{pad}for ({init.target} = {self._emit_expr(init.value, scope, obj)}; "
            f"{self._emit_expr(loop.condition, scope, obj)}; "
            f"{init.target} {op} {self._emit_expr(step.right, scope, obj)}) {{\n"
            f"{body}\n{pad}}}"
        )

    def _emit_stmt(self, stmt: ASTNode, scope: str, obj: str | None, tail_returns: bool, indent: int) -> str:
        stmt = self._normalize(stmt)
        pad = "  " * indent
        if isinstance(stmt, AssignmentNode):
            return f"{pad}{self._emit_store(stmt.target, stmt.value, scope, obj, field=bool(obj and stmt.target in self._fields(obj)))}"
        if isinstance(stmt, IndexAssignmentNode):
            target = self._emit_expr(stmt.target, scope, obj)
            index = self._emit_expr(stmt.index, scope, obj)
            value = self._cast(self._emit_expr(stmt.value, scope, obj), self._expr_type(stmt.value, scope, obj), self._index_store_type(stmt.target, scope, obj))
            if self._expr_type(stmt.target, scope, obj) == BITS:
                return f"{pad}{target}.set({index}, {value});"
            return f"{pad}{target}[{index}] = {value};"
        if isinstance(stmt, MemberAssignmentNode):
            target = self._emit_expr(stmt.target, scope, obj)
            value = self._emit_expr(stmt.value, scope, obj)
            arrow = "->" if self._expr_type(stmt.target, scope, obj)[0] == "obj" else "."
            return f"{pad}{target}{arrow}{stmt.member} = {value};"
        if isinstance(stmt, IfNode):
            cond = self._emit_expr(stmt.condition, scope, obj)
            then_b = self._emit_block(stmt.then_body, scope, obj, tail_returns=tail_returns, indent=indent + 1, declare=False)
            code = f"{pad}if ({cond}) {{\n{then_b}\n{pad}}}"
            if stmt.else_body:
                else_b = self._emit_block(stmt.else_body, scope, obj, tail_returns=tail_returns, indent=indent + 1, declare=False)
                code += f" else {{\n{else_b}\n{pad}}}"
            return code
        if isinstance(stmt, WhileNode):
            cond = self._emit_expr(stmt.condition, scope, obj)
            body = self._emit_block(stmt.body, scope, obj, tail_returns=False, indent=indent + 1, declare=False)
            return f"{pad}while ({cond}) {{\n{body}\n{pad}}}"
        if isinstance(stmt, ForNode):
            iterable = self._emit_expr(stmt.iterable, scope, obj)
            body = self._emit_block(stmt.body, scope, obj, tail_returns=False, indent=indent + 1, declare=False)
            return f"{pad}for (auto {stmt.var_name} : {iterable}) {{\n{body}\n{pad}}}"
        if isinstance(stmt, MatchNode):
            return self._emit_match(stmt, scope, obj, tail_returns, indent)
        if isinstance(stmt, SpawnNode):
            body = self._emit_block(stmt.body, scope, obj, tail_returns=False, indent=indent + 2, declare=False)
            return f"{pad}soma_join.jobs.push_back(std::async(std::launch::async, [&]() {{\n{body}\n{pad}}}));"
        if tail_returns and not isinstance(stmt, (CellDefNode,)):
            typ = self._expr_type(stmt, scope, obj)
            ret = self.return_types.get(scope, typ)
            expr = self._cast(self._emit_expr(stmt, scope, obj), typ, ret if ret != BOTTOM else typ)
            return f"{pad}return {expr};"
        return f"{pad}{self._emit_expr(stmt, scope, obj)};"

    def _emit_store(self, name: str, value: ASTNode, scope: str, obj: str | None, field: bool) -> str:
        target = f"soma_self->{name}" if scope.endswith(".__new__") and field else name
        dest = self._get(("field", obj, name)) if field and obj else self._lookup(scope, name)
        if (
            isinstance(value, CallNode)
            and isinstance(value.callee, IdentifierNode)
            and value.callee.name == "range"
            and len(value.args) == 1
        ):
            length = self._as_i64(self._emit_expr(value.args[0], scope, obj), self._expr_type(value.args[0], scope, obj))
            if dest == BITS:
                rhs = f"SomaBits({length})"
            elif dest == ("vec", F64):
                rhs = f"std::vector<double>(static_cast<size_t>({length}))"
            else:
                rhs = f"std::vector<int64_t>(static_cast<size_t>({length}))"
            return f"{target} = {rhs};"
        rhs = self._cast(self._emit_expr(value, scope, obj), self._expr_type(value, scope, obj), dest)
        return f"{target} = {rhs};"

    def _index_store_type(self, target: ASTNode, scope: str, obj: str | None):
        typ = self._expr_type(target, scope, obj)
        if typ == BITS:
            return BOOL
        if typ[0] == "vec":
            return typ[1]
        return I64

    def _emit_match(self, node: MatchNode, scope: str, obj: str | None, tail_returns: bool, indent: int) -> str:
        pad = "  " * indent
        subject = self._emit_expr(node.subject, scope, obj)
        lines = [f"{pad}{{", f"{pad}  auto soma_subject = {subject};"]
        for case in node.cases:
            body = self._emit_block(case.body, scope, obj, tail_returns=tail_returns, indent=indent + 2, declare=False)
            guard = self._emit_expr(case.guard, scope, obj) if case.guard is not None else "true"
            if isinstance(case.pattern, IdentifierNode) and case.pattern.name == "_":
                lines.append(f"{pad}  if ({guard}) {{\n{body}\n{pad}  }}")
            elif isinstance(case.pattern, IdentifierNode):
                lines.append(
                    f"{pad}  {{ auto {case.pattern.name} = soma_subject; if ({guard}) {{\n{body}\n{pad}  }} }}"
                )
            else:
                compared = self._emit_expr(case.pattern, scope, obj)
                lines.append(f"{pad}  if ((soma_subject == {compared}) && ({guard})) {{\n{body}\n{pad}  }}")
        lines.append(f"{pad}}}")
        return "\n".join(lines)

    def _emit_expr(self, node: ASTNode, scope: str, obj: str | None) -> str:
        if isinstance(node, LiteralNode):
            if isinstance(node.value, bool):
                return "true" if node.value else "false"
            if isinstance(node.value, str):
                escaped = (
                    node.value.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\t", "\\t")
                )
                return f'std::string("{escaped}")'
            if node.value is None:
                return "nullptr"
            if isinstance(node.value, float):
                text = repr(node.value)
                if "e" not in text and "." not in text:
                    text += ".0"
                return text
            return f"{int(node.value)}LL"
        if isinstance(node, IdentifierNode):
            if scope.endswith(".__new__") and obj and node.name in self._fields(obj):
                return f"soma_self->{node.name}"
            return node.name
        if isinstance(node, ListNode):
            elements = ", ".join(self._emit_expr(element, scope, obj) for element in node.elements)
            return f"std::vector<int64_t>{{{elements}}}"
        if isinstance(node, UnaryOpNode):
            inner = self._emit_expr(node.expr, scope, obj)
            if node.op == "not":
                return f"!({inner})"
            return f"(-{inner})"
        if isinstance(node, BinaryOpNode):
            left_t = self._expr_type(node.left, scope, obj)
            right_t = self._expr_type(node.right, scope, obj)
            left = self._emit_expr(node.left, scope, obj)
            right = self._emit_expr(node.right, scope, obj)
            op = {"and": "&&", "or": "||"}.get(node.op, node.op)
            if node.op == "^":
                return f"std::pow(static_cast<double>({left}), static_cast<double>({right}))"
            if node.op == "/":
                return f"(static_cast<double>({left}) / static_cast<double>({right}))"
            if node.op == "%" and (left_t == F64 or right_t == F64):
                return f"std::fmod(static_cast<double>({left}), static_cast<double>({right}))"
            if node.op == "+" and (left_t == STR or right_t == STR):
                return f"({self._as_str(left, left_t)} + {self._as_str(right, right_t)})"
            if node.op in ("==", "!=") and (self._is_none(node.right) or self._is_none(node.left)):
                side = right if self._is_none(node.right) else left
                other = left if self._is_none(node.right) else right
                return f"({other} {op} nullptr)" if False else f"({left if not self._is_none(node.left) else 'nullptr'} {op} {right if not self._is_none(node.right) else 'nullptr'})"
            return f"({left} {op} {right})"
        if isinstance(node, PipelineNode):
            if isinstance(node.right, CallNode):
                return self._emit_call(node.right.callee, [node.left, *node.right.args], scope, obj)
            return self._emit_call(node.right, [node.left], scope, obj)
        if isinstance(node, IndexAccessNode):
            target = self._emit_expr(node.target, scope, obj)
            index = self._emit_expr(node.index, scope, obj)
            if self._expr_type(node.target, scope, obj) == BITS:
                return f"{target}.get({index})"
            return f"{target}[{index}]"
        if isinstance(node, MemberAccessNode):
            target = self._emit_expr(node.target, scope, obj)
            if self._expr_type(node.target, scope, obj)[0] == "obj":
                return f"{target}->{node.member}"
            return f"{target}.{node.member}"
        if isinstance(node, CallNode):
            return self._emit_call(node.callee, node.args, scope, obj)
        if isinstance(node, MatchNode):
            return f"([&]() {{\n{self._emit_match(node, scope, obj, True, 0)}\n  return 0;\n}}())"
        raise NativeCompileError(f"cannot emit {type(node).__name__}")

    def _is_none(self, node: ASTNode) -> bool:
        return isinstance(node, LiteralNode) and node.value is None

    def _emit_call(self, callee: ASTNode, args: list[ASTNode], scope: str, obj: str | None) -> str:
        rendered = [self._emit_expr(arg, scope, obj) for arg in args]
        if isinstance(callee, IdentifierNode):
            name = callee.name
            if name == "sqrt":
                return f"soma_sqrt(static_cast<double>({rendered[0]}))"
            if name == "sin":
                return f"soma_sin(static_cast<double>({rendered[0]}))"
            if name == "cos":
                return f"soma_cos(static_cast<double>({rendered[0]}))"
            if name == "abs":
                typ = self._expr_type(args[0], scope, obj)
                if typ == F64:
                    return f"soma_abs_f({rendered[0]})"
                return f"soma_abs_i(static_cast<int64_t>({rendered[0]}))"
            if name == "str":
                return self._as_str(rendered[0], self._expr_type(args[0], scope, obj))
            if name == "len":
                return f"static_cast<int64_t>({rendered[0]}.size())"
            if name == "int":
                return f"static_cast<int64_t>({rendered[0]})"
            if name == "float":
                return f"static_cast<double>({rendered[0]})"
            if name == "perf" or name == "time":
                return "perf()"
            if name == "print":
                return f"print({', '.join(rendered)})"
            if name == "range":
                length = self._as_i64(rendered[0], self._expr_type(args[0], scope, obj))
                return f"std::vector<int64_t>(static_cast<size_t>({length}))"
            if name in self.objects:
                return f"{name}_call({', '.join(rendered)})"
            return f"{name}({', '.join(rendered)})"
        if isinstance(callee, MemberAccessNode):
            target = self._emit_expr(callee.target, scope, obj)
            arrow = "->" if self._expr_type(callee.target, scope, obj)[0] == "obj" else "."
            return f"{target}{arrow}{callee.member}({', '.join(rendered)})"
        raise NativeCompileError("cannot emit call")

    def _as_str(self, expr: str, typ) -> str:
        if typ == STR:
            return expr
        if typ == F64:
            return f"soma_str(static_cast<double>({expr}))"
        if typ == BOOL:
            return f"soma_str(static_cast<bool>({expr}))"
        if typ == I64 or typ == BOTTOM:
            return f"soma_str(static_cast<int64_t>({expr}))"
        return f"soma_str({expr})"

    def _as_i64(self, expr: str, typ) -> str:
        if typ == I64 or typ == BOTTOM:
            return expr
        return f"static_cast<int64_t>({expr})"

    def _cast(self, expr: str, src, dest) -> str:
        if dest == BOTTOM or dest == ANY or src == dest:
            return expr
        if dest == F64 and src != F64:
            return f"static_cast<double>({expr})"
        if dest == I64 and src != I64:
            return f"static_cast<int64_t>({expr})"
        if dest == BOOL and src != BOOL:
            return f"static_cast<bool>({expr})"
        return expr
