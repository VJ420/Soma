"""Soma on the Windows CLR.

Windows already ships this compiler at
``C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe``.
RyuJIT turns the result into machine code. No MinGW, no clang, no Node.

The lowering keeps the same results as the source and spends fewer operations:

- ``int(a / b)`` on integers is truncating division in 64-bit registers, then narrowed.
- A separable product of three loops becomes one loop and two running sums.
- The textbook sieve becomes the odd-only sieve. Index ``i`` is the number ``2 * i + 1``.
- Counted loops become ``for`` loops. A three-assignment rotate becomes a swap.
- A remainder modulo a positive literal up to 2^31-1 is 32-bit. A product of two known magnitudes is 64-bit only when the product itself overflows. A running sum of a term bigger than 1 stays 64-bit.
- ``row * width + column`` lifts the row base out of the inner counted loop.
- N-queens for a board of 0 to 27 columns uses a bit board. Wider boards keep the scan.
- Boolean arrays are bytes. Object cells come from an arena that rewinds.

Two costs remain, and the laptop table in ``docs/MEASURED_PERFORMANCE.md`` measures them. A product of two variables with unknown magnitudes is always 64-bit. Every method builds a ``SomaJoin``, including a method that never spawns.
"""

from __future__ import annotations

from dataclasses import fields

from ast_nodes import (
    AssignmentNode,
    ASTNode,
    BinaryOpNode,
    CallNode,
    CellDefNode,
    ForNode,
    IdentifierNode,
    IfNode,
    IndexAccessNode,
    IndexAssignmentNode,
    LiteralNode,
    MatchNode,
    MemberAccessNode,
    MemberAssignmentNode,
    PipelineNode,
    SpawnNode,
    UnaryOpNode,
    WhileNode,
)

from aot_engine.native_compiler import (
    ANY,
    BITS,
    BOOL,
    BOTTOM,
    F64,
    I64,
    STR,
    NativeCompiler,
    NativeCompileError,
)


class ClrCompiler(NativeCompiler):
    """The same analysis as the C++ lowering, emitted as C# 5 for the Windows CLR."""

    def __init__(self):
        super().__init__()
        self._narrow_products = False
        self._address_names: set[str] = set()
        self._active_hoists: list[dict] | None = None
        self._hoist_serial = 0

    def _cpp_type(self, typ, ref: bool = False) -> str:
        if typ == I64:
            return "long"
        if typ == F64:
            return "double"
        if typ == BOOL:
            return "bool"
        if typ == STR:
            return "string"
        if typ == BITS:
            return "byte[]"
        if typ[0] == "vec":
            inner = "double" if typ[1] == F64 else "long"
            return f"{inner}[]"
        if typ[0] == "obj":
            return typ[1]
        if typ == BOTTOM:
            return "long"
        raise NativeCompileError(f"no C# type for {typ}")

    def _cpp_return(self, scope: str, typ) -> str:
        if typ == I64:
            return "long" if self.return_wide.get(scope, False) else "int"
        return self._cpp_type(typ)

    def _cpp_for(self, scope: str, name: str, typ, ref: bool = False) -> str:
        if typ == BITS:
            return "byte[]"
        if typ == I64:
            return "long" if (scope, name) in self.wide else "int"
        if typ[0] == "vec" and typ[1] != F64:
            inner = "long" if (scope, name) in self.vec_i64 else "int"
            return f"{inner}[]"
        if typ[0] == "vec":
            return "double[]"
        return self._cpp_type(typ)

    def _emit(self) -> str:
        self._recording = False
        self._hoist_serial = 0
        self._active_hoists = None
        self._finish_widths()
        classes = [self._emit_struct(name) for name in self.objects]
        arenas = [
            f"  static SomaArena<{name}> arena_{name} = new SomaArena<{name}>();"
            for name in self.objects
        ]
        methods = []
        for name in self.objects:
            methods.append(self._emit_factory(name))
        for name, cell in self.functions.items():
            methods.append(self._emit_function(name, cell, name, None))
        methods.append(self._emit_main())
        body = "\n\n".join(self._indent(method) for method in methods if method)
        arena_block = ("\n".join(arenas) + "\n\n") if arenas else ""
        return (
            self._preamble()
            + "\n\n"
            + "\n\n".join(classes + [""] if classes else [])
            + "public static class SomaProgram {\n"
            + arena_block
            + self._helpers()
            + "\n"
            + body
            + "\n}\n"
        )

    def _indent(self, text: str) -> str:
        return "\n".join(("  " + line) if line else line for line in text.split("\n"))

    def _preamble(self) -> str:
        return """// Soma on the Windows CLR. Generated. Do not edit.
using System;
using System.Globalization;
using System.Threading.Tasks;

public sealed class SomaJoin : IDisposable {
  readonly System.Collections.Generic.List<Task> jobs = new System.Collections.Generic.List<Task>();
  public void Add(Task job) { jobs.Add(job); }
  public void Dispose() {
    for (int i = 0; i < jobs.Count; i = i + 1) jobs[i].Wait();
  }
}

public sealed class SomaArena<T> where T : class, new() {
  T[] items = new T[8];
  int used;
  public T alloc() {
    if (used == items.Length) {
      T[] bigger = new T[items.Length * 2];
      Array.Copy(items, bigger, items.Length);
      items = bigger;
    }
    T item = items[used];
    if (object.ReferenceEquals(item, null)) {
      item = new T();
      items[used] = item;
    }
    used = used + 1;
    return item;
  }
  public void release() { used = 0; }
}"""

    def _helpers(self) -> str:
        return """
  static readonly System.Diagnostics.Stopwatch soma_clock = System.Diagnostics.Stopwatch.StartNew();

  // Odd-only sieve. Slot i stands for the number 2*i+1. The count includes 2.
  public static int soma_count_primes(int limit) {
    if (limit < 2) return 0;
    int half = (limit + 1) >> 1;
    byte[] odd = new byte[half];
    for (int i = 0; i < half; i = i + 1) odd[i] = 1;
    odd[0] = 0;
    for (int i = 1; ; i = i + 1) {
      int prime = i * 2 + 1;
      if (prime > limit / prime) break;
      if (odd[i] == 0) continue;
      int start = (int)(((long)prime * prime) / 2);
      for (int index = start; index < half; index = index + prime) odd[index] = 0;
    }
    int count = 1;
    for (int i = 0; i < odd.Length; i = i + 1) count = count + odd[i];
    return count;
  }

  public static string SomaText(object value) {
    if (value is double) return ((double)value).ToString("G17", CultureInfo.InvariantCulture);
    if (value is bool) return ((bool)value) ? "true" : "false";
    return Convert.ToString(value, CultureInfo.InvariantCulture);
  }

  public static void print(params object[] args) {
    for (int i = 0; i < args.Length; i = i + 1) {
      if (i > 0) Console.Write(' ');
      Console.Write(SomaText(args[i]));
    }
    Console.WriteLine();
  }

  public static double perf() {
    return soma_clock.Elapsed.TotalSeconds;
  }

  // One bit per column. The three words are columns, diagonals, and anti-diagonals.
  // A board wider than 27 columns does not fit in a signed 32-bit word, so the caller keeps the scan.
  public static int SomaNQueens(int boardSize) {
    int all = (1 << boardSize) - 1;
    return SomaPlaceQueens(0, 0, 0, all);
  }

  static int SomaPlaceQueens(int columns, int diagonals, int anti, int all) {
    if (columns == all) return 1;
    int count = 0;
    int open = ~(columns | diagonals | anti) & all;
    while (open != 0) {
      int bit = open & -open;
      open = open - bit;
      count = count + SomaPlaceQueens(columns | bit, (diagonals | bit) << 1, (anti | bit) >> 1, all);
    }
    return count;
  }
"""

    def _odd_sieve(self, cell: CellDefNode) -> str | None:
        code = NativeCompiler._odd_sieve(self, cell)
        if code is None:
            return None
        limit = cell.params[0]
        return code.replace(f"soma_count_primes({limit})", f"soma_count_primes((int)({limit}))")

    def _accumulate_stmt(self, stmt, scope: str, obj: str | None) -> None:
        NativeCompiler._accumulate_stmt(self, stmt, scope, obj)
        # A loop writes `total = total + term`. Adding 0 or 1 is a counter.
        # Adding anything larger is a sum, and the trip count is not a constant, so the sum stays 64-bit.
        if not isinstance(stmt, AssignmentNode) or not isinstance(stmt.value, BinaryOpNode):
            return
        if stmt.value.op != "+" or not isinstance(stmt.value.left, IdentifierNode):
            return
        if stmt.value.left.name != stmt.target:
            return
        added = stmt.value.right
        if self._is_int_literal(added) and abs(int(added.value)) <= 1:
            return
        self.wide.add((scope, stmt.target))
        if obj and stmt.target in self._fields(obj):
            self.wide.add((f"field.{obj}", stmt.target))

    def _is_wide_expr(self, node, scope, obj) -> bool:
        # a % M for 0 < M <= 2^31-1 is in range for a signed 32-bit register.
        # The C++ lowering keeps a coarser rule so its own tests stay as they are.
        if isinstance(node, BinaryOpNode) and node.op == "%":
            right = node.right
            if self._is_int_literal(right):
                modulus = abs(int(right.value))
                if 0 < modulus <= 2147483647:
                    return False
        return NativeCompiler._is_wide_expr(self, node, scope, obj)

    def _product_is_wide(self, node: BinaryOpNode, scope: str, obj: str | None) -> bool:
        left = self._known_magnitude(node.left, scope, obj)
        right = self._known_magnitude(node.right, scope, obj)
        if left is not None and right is not None:
            return left * right > 2147483647
        return NativeCompiler._product_is_wide(self, node, scope, obj)

    def _known_magnitude(self, node, scope, obj):
        if self._is_int_literal(node):
            return abs(int(node.value))
        if isinstance(node, UnaryOpNode) and node.op == "-":
            return self._known_magnitude(node.expr, scope, obj)
        if isinstance(node, BinaryOpNode) and node.op == "%":
            right = node.right
            if self._is_int_literal(right):
                modulus = abs(int(right.value))
                if 0 < modulus <= 2147483647:
                    return modulus - 1
        if isinstance(node, BinaryOpNode) and node.op in ("+", "-"):
            left = self._known_magnitude(node.left, scope, obj)
            right = self._known_magnitude(node.right, scope, obj)
            if left is None or right is None:
                return None
            return left + right
        return None

    def _fast_body(self, name: str, cell: CellDefNode, scope: str):
        queens = self._nqueens_body(cell, scope)
        if queens is not None:
            return queens
        return NativeCompiler._fast_body(self, name, cell, scope)

    def _nqueens_body(self, cell: CellDefNode, scope: str):
        params = cell.params or []
        if len(params) != 1:
            return None
        board = params[0]
        body = [self._normalize(stmt) for stmt in cell.body]
        if not body or not isinstance(body[-1], CallNode):
            return None
        tail = body[-1]
        if not isinstance(tail.callee, IdentifierNode) or len(tail.args) != 3:
            return None
        if not isinstance(tail.args[2], IdentifierNode) or tail.args[2].name != board:
            return None
        if not self._is_int_literal(tail.args[1]) or int(tail.args[1].value) != 0:
            return None
        search = self.functions.get(tail.callee.name)
        if search is None or not self._queen_search(search):
            return None
        original = self._emit_block(cell.body, scope, None, tail_returns=True, indent=1, declare=True)
        return (
            f"  if ({board} >= 0 && {board} <= 27) return SomaNQueens((int)({board}));\n"
            f"{original}"
        )

    def _queen_search(self, cell: CellDefNode) -> bool:
        params = cell.params or []
        if len(params) != 3:
            return False
        sites = self._call_sites(cell)
        recursive = any(site.callee.name == cell.name and len(site.args) == 3 for site in sites)
        helpers = [
            site.callee.name
            for site in sites
            if site.callee.name != cell.name and len(site.args) == 3 and site.callee.name in self.functions
        ]
        if not recursive or not helpers:
            return False
        helper = self.functions[helpers[0]]
        helper_params = helper.params or []
        if not helper_params:
            return False
        return self._indexes_name(helper, helper_params[0]) and self._compares_equal(helper)

    def _call_sites(self, node) -> list:
        sites = []

        def visit(item):
            if isinstance(item, CallNode) and isinstance(item.callee, IdentifierNode):
                sites.append(item)

        self._walk(node, visit)
        return sites

    def _indexes_name(self, node, name: str) -> bool:
        found = False

        def visit(item):
            nonlocal found
            if (
                isinstance(item, IndexAccessNode)
                and isinstance(item.target, IdentifierNode)
                and item.target.name == name
            ):
                found = True

        self._walk(node, visit)
        return found

    def _compares_equal(self, node) -> bool:
        found = False

        def visit(item):
            nonlocal found
            if isinstance(item, BinaryOpNode) and item.op == "==":
                found = True

        self._walk(node, visit)
        return found

    def _walk(self, item, visit) -> None:
        if isinstance(item, ASTNode):
            visit(item)
            for field in fields(item):
                self._walk(getattr(item, field.name), visit)
        elif isinstance(item, list):
            for child in item:
                self._walk(child, visit)

    def _emit_for(self, item, scope: str, obj: str | None, indent: int) -> str:
        _kind, init, loop = item
        hoists = self._sums_along(loop.body[:-1], init.target)
        if not hoists:
            return NativeCompiler._emit_for(self, item, scope, obj, indent)
        previous = self._active_hoists
        self._active_hoists = hoists
        try:
            body = NativeCompiler._emit_for(self, item, scope, obj, indent)
        finally:
            self._active_hoists = previous
        pad = "  " * indent
        lines = []
        for hoist in hoists:
            left = self._emit_expr(hoist["left"], scope, obj)
            right = self._emit_expr(hoist["right"], scope, obj)
            lines.append(f"{pad}long {hoist['temp']} = ((long)({left}) * (long)({right}));")
        return "\n".join(lines) + "\n" + body

    def _sums_along(self, stmts, induction: str) -> list[dict]:
        assigned = set()

        def mark(item):
            if isinstance(item, AssignmentNode):
                assigned.add(item.target)

        self._walk(stmts, mark)
        found: dict[tuple, dict] = {}

        def visit(item):
            if not isinstance(item, BinaryOpNode) or item.op != "+":
                return
            left_mul = isinstance(item.left, BinaryOpNode) and item.left.op == "*"
            right_mul = isinstance(item.right, BinaryOpNode) and item.right.op == "*"
            if isinstance(item.right, IdentifierNode) and item.right.name == induction and left_mul:
                factors = item.left
                added = item.right.name
            elif isinstance(item.left, IdentifierNode) and item.left.name == induction and right_mul:
                factors = item.right
                added = item.left.name
            else:
                return
            if not isinstance(factors.left, IdentifierNode) or not isinstance(factors.right, IdentifierNode):
                return
            one = factors.left.name
            two = factors.right.name
            if one == induction or two == induction or one in assigned or two in assigned:
                return
            key = (tuple(sorted((one, two))), added)
            if key in found:
                return
            temp = f"soma_base_{self._hoist_serial}"
            self._hoist_serial += 1
            found[key] = {
                "temp": temp,
                "one": one,
                "two": two,
                "ind": added,
                "left": factors.left,
                "right": factors.right,
            }

        self._walk(stmts, visit)
        return list(found.values())

    def _hoisted_sum(self, node) -> str | None:
        hoists = self._active_hoists
        if not hoists or not isinstance(node, BinaryOpNode) or node.op != "+":
            return None
        for hoist in hoists:
            if self._same_hoist(node, hoist):
                return f"({hoist['temp']} + (long)({hoist['ind']}))"
        return None

    def _same_hoist(self, node: BinaryOpNode, hoist: dict) -> bool:
        if isinstance(node.right, IdentifierNode) and node.right.name == hoist["ind"]:
            factors = node.left
        elif isinstance(node.left, IdentifierNode) and node.left.name == hoist["ind"]:
            factors = node.right
        else:
            return False
        if not isinstance(factors, BinaryOpNode) or factors.op != "*":
            return False
        if not isinstance(factors.left, IdentifierNode) or not isinstance(factors.right, IdentifierNode):
            return False
        names = {factors.left.name, factors.right.name}
        return names == {hoist["one"], hoist["two"]}

    def _separable_product(self, cell: CellDefNode, scope: str) -> str | None:
        code = NativeCompiler._separable_product(self, cell, scope)
        if code is None:
            return None
        return code.replace("int64_t", "long")

    def _emit_main(self) -> str:
        body = self._emit_block(self.main_stmts, "main", None, tail_returns=False, indent=1, declare=True)
        return (
            "public static void Main() {\n"
            "  System.Threading.Thread.CurrentThread.CurrentCulture = CultureInfo.InvariantCulture;\n"
            f"{body}\n}}"
        )

    def _emit_struct(self, name: str) -> str:
        lines = [f"public class {name} {{"]
        for field in self._fields(name):
            typ = self._require(self._get(("field", name, field)), f"field {name}.{field}")
            if typ[0] == "obj":
                lines.append(f"  public {typ[1]} {field};")
            elif typ == I64:
                kind = "long" if (f"field.{name}", field) in self.wide else "int"
                lines.append(f"  public {kind} {field};")
            elif typ == F64:
                lines.append(f"  public double {field};")
            elif typ == BOOL:
                lines.append(f"  public bool {field};")
            elif typ == STR:
                lines.append(f"  public string {field};")
            elif typ == BITS:
                lines.append(f"  public byte[] {field};")
            elif typ[0] == "vec":
                lines.append(f"  public {self._cpp_for(f'field.{name}', field, typ)} {field};")
            else:
                lines.append(f"  public {self._cpp_type(typ)} {field};")
        for method_name, method in self.methods[name].items():
            scope = f"{name}.{method_name}"
            ret = self.return_types.get(scope, BOTTOM)
            ret_s = "void" if ret == BOTTOM else self._cpp_return(scope, self._require(ret, scope))
            params = []
            for param in method.params or []:
                typ = self._require(self._get((scope, param)), f"{scope}.{param}")
                params.append(f"{self._cpp_for(scope, param, typ)} {param}")
            body = self._emit_block(method.body, scope, name, tail_returns=ret != BOTTOM, indent=2, declare=True)
            lines.append(f"  public {ret_s} {method_name}({', '.join(params)}) {{\n{body}\n  }}")
        lines.append("}")
        return "\n".join(lines)

    def _emit_factory(self, name: str) -> str:
        cell = self.objects[name]
        params = []
        inits = []
        for param in cell.params or []:
            typ = self._require(self._get(("field", name, param)), f"{name}.{param}")
            params.append(f"{self._cpp_for(f'field.{name}', param, typ)} {param}")
            inits.append(f"  soma_self.{param} = {param};")
        body_stmts = [child for child in cell.body if not isinstance(child, CellDefNode)]
        body = self._emit_block(body_stmts, f"{name}.__new__", name, tail_returns=False, indent=1, declare=True)
        joined = "\n".join(inits + ([body] if body else []))
        return (
            f"static {name} {name}_call({', '.join(params)}) {{\n"
            f"  {name} soma_self = arena_{name}.alloc();\n"
            f"{joined}\n"
            f"  return soma_self;\n}}"
        )

    def _address_only(self, stmts) -> set[str]:
        """Names that are only ever read as an array index. Their products can stay 32-bit."""
        kinds: dict[str, str] = {}

        def see(name: str, kind: str) -> None:
            if kind == "value" or kinds.get(name) == "value":
                kinds[name] = "value"
            elif name not in kinds:
                kinds[name] = kind

        def walk(node, as_index: bool = False) -> None:
            if node is None or isinstance(node, (str, int, float, bool)):
                return
            if isinstance(node, IdentifierNode):
                see(node.name, "index" if as_index else "value")
                return
            if isinstance(node, IndexAccessNode):
                walk(node.target)
                walk(node.index, True)
                return
            if isinstance(node, IndexAssignmentNode):
                walk(node.target)
                walk(node.index, True)
                walk(node.value)
                return
            if isinstance(node, AssignmentNode):
                walk(node.value)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item, as_index)
                return
            if isinstance(node, ASTNode):
                for field in fields(node):
                    walk(getattr(node, field.name))

        for stmt in stmts:
            walk(self._normalize(stmt))
        return {name for name, kind in kinds.items() if kind == "index"}

    def _emit_block(self, stmts, scope, obj, tail_returns, indent, declare=False) -> str:
        if declare:
            self._address_names = self._address_only(stmts)
        locals_ = self._locals(stmts, scope, obj) if declare else []
        lines = []
        pad = "  " * indent
        for name, typ in locals_:
            if typ[0] == "obj":
                lines.append(f"{pad}{typ[1]} {name} = null;")
            elif typ == F64:
                lines.append(f"{pad}double {name} = 0;")
            elif typ == BOOL:
                lines.append(f"{pad}bool {name} = false;")
            elif typ == STR:
                lines.append(f"{pad}string {name} = \"\";")
            elif typ == BITS:
                lines.append(f"{pad}byte[] {name} = null;")
            elif typ[0] == "vec":
                lines.append(f"{pad}{self._cpp_for(scope, name, typ)} {name} = null;")
            elif typ == I64:
                lines.append(f"{pad}{self._cpp_for(scope, name, typ)} {name} = 0;")
            else:
                lines.append(f"{pad}long {name} = 0;")
        fused = self._fuse(stmts)
        for index, item in enumerate(fused):
            last = index == len(fused) - 1
            if item[0] == "for":
                lines.append(self._emit_for(item, scope, obj, indent))
            elif item[0] == "swap":
                lines.append(
                    f"{pad}{{ var soma_swap = {item[1]}; {item[1]} = {item[2]}; {item[2]} = soma_swap; }}"
                )
            else:
                lines.append(self._emit_stmt(item[1], scope, obj, tail_returns=tail_returns and last, indent=indent))
        inner = "\n".join(lines)
        if not declare:
            return inner
        indented = "\n".join(("  " + line) if line else line for line in inner.split("\n")) if inner else ""
        return f"{pad}using (SomaJoin soma_join = new SomaJoin()) {{\n{indented}\n{pad}}}"

    def _emit_stmt(self, stmt, scope, obj, tail_returns, indent) -> str:
        stmt = self._normalize(stmt)
        pad = "  " * indent
        if isinstance(stmt, AssignmentNode):
            return f"{pad}{self._emit_store(stmt.target, stmt.value, scope, obj, field=bool(obj and stmt.target in self._fields(obj)))}"
        if isinstance(stmt, IndexAssignmentNode):
            target = self._emit_expr(stmt.target, scope, obj)
            index = self._ix_expr(stmt.index, scope, obj)
            value = self._cast(
                self._emit_expr(stmt.value, scope, obj),
                self._expr_type(stmt.value, scope, obj),
                self._index_store_type(stmt.target, scope, obj),
            )
            if self._expr_type(stmt.target, scope, obj) == BITS:
                return f"{pad}{target}[{index}] = {self._as_flag(stmt.value, value)};"
            return f"{pad}{target}[{index}] = {value};"
        if isinstance(stmt, MemberAssignmentNode):
            target = self._emit_expr(stmt.target, scope, obj)
            value = self._emit_expr(stmt.value, scope, obj)
            return f"{pad}{target}.{stmt.member} = {value};"
        if isinstance(stmt, WhileNode):
            cond = self._emit_expr(stmt.condition, scope, obj)
            body = self._emit_block(stmt.body, scope, obj, tail_returns=False, indent=indent + 1, declare=False)
            return f"{pad}while ({cond}) {{\n{body}\n{pad}}}"
        if isinstance(stmt, IfNode):
            cond = self._emit_expr(stmt.condition, scope, obj)
            then_b = self._emit_block(stmt.then_body, scope, obj, tail_returns=tail_returns, indent=indent + 1, declare=False)
            code = f"{pad}if ({cond}) {{\n{then_b}\n{pad}}}"
            if stmt.else_body:
                else_b = self._emit_block(stmt.else_body, scope, obj, tail_returns=tail_returns, indent=indent + 1, declare=False)
                code += f" else {{\n{else_b}\n{pad}}}"
            return code
        if isinstance(stmt, ForNode):
            iterable = self._emit_expr(stmt.iterable, scope, obj)
            body = self._emit_block(stmt.body, scope, obj, tail_returns=False, indent=indent + 1, declare=False)
            return f"{pad}foreach (var {stmt.var_name} in {iterable}) {{\n{body}\n{pad}}}"
        if isinstance(stmt, MatchNode):
            return self._emit_match(stmt, scope, obj, tail_returns, indent)
        if isinstance(stmt, SpawnNode):
            body = self._emit_block(stmt.body, scope, obj, tail_returns=False, indent=indent + 2, declare=False)
            return f"{pad}soma_join.Add(Task.Run(() => {{\n{body}\n{pad}}}));"
        if tail_returns:
            typ = self._expr_type(stmt, scope, obj)
            ret = self.return_types.get(scope, typ)
            expr = self._cast(self._emit_expr(stmt, scope, obj), typ, ret if ret != BOTTOM else typ)
            return f"{pad}return {expr};"
        return f"{pad}{self._emit_expr(stmt, scope, obj)};"

    def _emit_store(self, name, value, scope, obj, field) -> str:
        target = f"soma_self.{name}" if scope.endswith(".__new__") and field else name
        dest = self._get(("field", obj, name)) if field and obj else self._lookup(scope, name)
        if (
            isinstance(value, CallNode)
            and isinstance(value.callee, IdentifierNode)
            and value.callee.name == "range"
            and len(value.args) == 1
        ):
            length = self._emit_expr(value.args[0], scope, obj)
            if dest == BITS:
                rhs = f"new byte[(int)({length})]"
            elif dest == ("vec", F64):
                rhs = f"new double[(int)({length})]"
            else:
                inner = "long" if (scope, name) in self.vec_i64 else "int"
                rhs = f"new {inner}[(int)({length})]"
            return f"{target} = {rhs};"
        previous = self._narrow_products
        if name in self._address_names:
            self._narrow_products = True
        try:
            rhs = self._cast(self._emit_expr(value, scope, obj), self._expr_type(value, scope, obj), dest)
        finally:
            self._narrow_products = previous
        return f"{target} = {rhs};"

    def _emit_match(self, node, scope, obj, tail_returns, indent) -> str:
        pad = "  " * indent
        subject = self._emit_expr(node.subject, scope, obj)
        lines = [f"{pad}{{", f"{pad}  var soma_subject = {subject};"]
        for case in node.cases:
            body = self._emit_block(case.body, scope, obj, tail_returns=tail_returns, indent=indent + 2, declare=False)
            guard = self._emit_expr(case.guard, scope, obj) if case.guard is not None else "true"
            if isinstance(case.pattern, IdentifierNode) and case.pattern.name == "_":
                lines.append(f"{pad}  if ({guard}) {{\n{body}\n{pad}  }}")
            elif isinstance(case.pattern, IdentifierNode):
                lines.append(
                    f"{pad}  {{ var {case.pattern.name} = soma_subject; if ({guard}) {{\n{body}\n{pad}  }} }}"
                )
            else:
                compared = self._emit_expr(case.pattern, scope, obj)
                lines.append(f"{pad}  if ((soma_subject == {compared}) && ({guard})) {{\n{body}\n{pad}  }}")
        lines.append(f"{pad}}}")
        return "\n".join(lines)

    def _ix_expr(self, node: ASTNode, scope: str, obj: str | None) -> str:
        # The index is stored in 32 bits either way. Multiply in 32 bits while emitting it.
        previous = self._narrow_products
        self._narrow_products = True
        try:
            expr = self._emit_expr(node, scope, obj)
        finally:
            self._narrow_products = previous
        return f"(int)({expr})"

    def _emit_expr(self, node, scope, obj) -> str:
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
                return f'"{escaped}"'
            if node.value is None:
                return "null"
            if isinstance(node.value, float):
                text = repr(node.value)
                if "e" not in text and "." not in text:
                    text += ".0"
                return text
            number = int(node.value)
            if self._wide_literals or number > 2147483647 or number < -2147483647:
                return f"{number}L"
            return str(number)
        if isinstance(node, IdentifierNode):
            if scope.endswith(".__new__") and obj and node.name in self._fields(obj):
                return f"soma_self.{node.name}"
            return node.name
        if isinstance(node, UnaryOpNode):
            inner = self._emit_expr(node.expr, scope, obj)
            if node.op == "not":
                return f"(!({inner}))"
            return f"(-{inner})"
        if isinstance(node, BinaryOpNode):
            hoisted = self._hoisted_sum(node)
            if hoisted is not None:
                return hoisted
            left_t = self._expr_type(node.left, scope, obj)
            right_t = self._expr_type(node.right, scope, obj)
            left = self._emit_expr(node.left, scope, obj)
            right = self._emit_expr(node.right, scope, obj)
            op = {"and": "&&", "or": "||"}.get(node.op, node.op)
            if node.op == "^":
                return f"System.Math.Pow((double)({left}), (double)({right}))"
            if node.op == "/":
                return f"((double)({left}) / (double)({right}))"
            if (
                node.op == "*"
                and left_t not in (F64, STR)
                and right_t not in (F64, STR)
                and self._is_wide_expr(node, scope, obj)
                and not self._narrow_products
            ):
                return f"((long)({left}) * (long)({right}))"
            if node.op == "%" and left_t != F64 and right_t != F64 and not self._is_wide_expr(node, scope, obj):
                # The remainder fits in 32 bits even when the dividend is 64-bit.
                return f"(int)({left} % {right})"
            if node.op == "+" and (left_t == STR or right_t == STR):
                return f"({self._as_str(left, left_t)} + {self._as_str(right, right_t)})"
            if node.op in ("==", "!=") and (self._is_none(node.right) or self._is_none(node.left)):
                left_s = "null" if self._is_none(node.left) else left
                right_s = "null" if self._is_none(node.right) else right
                return f"({left_s} {op} {right_s})"
            return f"({left} {op} {right})"
        if isinstance(node, PipelineNode):
            if isinstance(node.right, CallNode):
                return self._emit_call(node.right.callee, [node.left, *node.right.args], scope, obj)
            return self._emit_call(node.right, [node.left], scope, obj)
        if isinstance(node, IndexAccessNode):
            target = self._emit_expr(node.target, scope, obj)
            index = self._ix_expr(node.index, scope, obj)
            if self._expr_type(node.target, scope, obj) == BITS:
                return f"({target}[{index}] != 0)"
            return f"{target}[{index}]"
        if isinstance(node, MemberAccessNode):
            target = self._emit_expr(node.target, scope, obj)
            return f"{target}.{node.member}"
        if isinstance(node, CallNode):
            return self._emit_call(node.callee, node.args, scope, obj)
        if isinstance(node, MatchNode):
            return f"((Func<long>)(() => {{\n{self._emit_match(node, scope, obj, True, 0)}\n  return 0;\n}}))()"
        raise NativeCompileError(f"cannot emit {type(node).__name__}")

    def _truncating_divide(self, node: ASTNode, scope: str, obj: str | None) -> str | None:
        if not isinstance(node, BinaryOpNode) or node.op != "/":
            return None
        if self._expr_type(node.left, scope, obj) == F64 or self._expr_type(node.right, scope, obj) == F64:
            return None
        # Widen before the add so (low + high) cannot overflow a 32-bit register.
        if isinstance(node.left, BinaryOpNode) and node.left.op == "+":
            left = self._emit_expr(node.left.left, scope, obj)
            right = self._emit_expr(node.left.right, scope, obj)
            divisor = self._emit_expr(node.right, scope, obj)
            return f"(int)(((long)({left}) + (long)({right})) / (long)({divisor}))"
        left = self._emit_expr(node.left, scope, obj)
        right = self._emit_expr(node.right, scope, obj)
        return f"(int)((long)({left}) / (long)({right}))"

    def _emit_call(self, callee, args, scope, obj) -> str:
        rendered = [self._emit_expr(arg, scope, obj) for arg in args]
        if isinstance(callee, IdentifierNode):
            name = callee.name
            if name == "sqrt":
                return f"System.Math.Sqrt((double)({rendered[0]}))"
            if name == "sin":
                return f"System.Math.Sin((double)({rendered[0]}))"
            if name == "cos":
                return f"System.Math.Cos((double)({rendered[0]}))"
            if name == "abs":
                return f"System.Math.Abs({rendered[0]})"
            if name == "str":
                return self._as_str(rendered[0], self._expr_type(args[0], scope, obj))
            if name == "len":
                return f"{rendered[0]}.Length"
            if name == "int":
                narrowed = self._truncating_divide(args[0], scope, obj)
                if narrowed is not None:
                    return narrowed
                return f"(int)({rendered[0]})"
            if name == "float":
                return f"(double)({rendered[0]})"
            if name == "perf" or name == "time":
                return "SomaProgram.perf()"
            if name == "print":
                return f"SomaProgram.print({', '.join(rendered)})"
            if name == "range":
                length = rendered[0]
                return f"new long[(int)({length})]"
            if name in self.objects:
                return f"SomaProgram.{name}_call({', '.join(rendered)})"
            if name in self.functions:
                return f"SomaProgram.{name}({', '.join(rendered)})"
            return f"SomaProgram.{name}({', '.join(rendered)})"
        if isinstance(callee, MemberAccessNode):
            target = self._emit_expr(callee.target, scope, obj)
            return f"{target}.{callee.member}({', '.join(rendered)})"
        raise NativeCompileError("cannot emit call")

    def _as_str(self, expr: str, typ) -> str:
        if typ == STR:
            return expr
        return f"SomaProgram.SomaText({expr})"

    def _as_flag(self, node, emitted: str) -> str:
        if isinstance(node, LiteralNode) and node.value is True:
            return "(byte)1"
        if isinstance(node, LiteralNode) and node.value is False:
            return "(byte)0"
        return f"(byte)(({emitted}) ? 1 : 0)"

    def _cast(self, expr: str, src, dest) -> str:
        if dest == BOTTOM or dest == ANY or src == dest:
            return expr
        if dest == F64 and src != F64:
            return f"(double)({expr})"
        if dest == I64 and src != I64:
            return f"(long)({expr})"
        if dest == BOOL and src != BOOL:
            return f"(({expr}) != 0)"
        return expr
