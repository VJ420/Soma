"""
Fractal Gradual Type System and Static Contract Inference Subsystem.
Provides zero-cost optional static type contracts with Bidirectional Type Inference.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union
from ast_nodes import (
    ASTNode, ProgramNode, CellDefNode, AssignmentNode, BinaryOpNode,
    UnaryOpNode, LiteralNode, IdentifierNode, CallNode, ListNode
)

class TypeKind(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "str"
    BOOL = "bool"
    NONE = "none"
    LIST = "list"
    MAP = "map"
    CELL = "cell"
    FUNCTION = "function"
    ANY = "any"

@dataclass(slots=True, frozen=True)
class FractalType:
    kind: TypeKind
    subtypes: List['FractalType'] = field(default_factory=list)
    cell_name: Optional[str] = None

    def __repr__(self) -> str:
        if self.kind == TypeKind.LIST and self.subtypes:
            return f"list[{self.subtypes[0]}]"
        if self.kind == TypeKind.CELL:
            return f"Cell<{self.cell_name or 'Anonymous'}>"
        return self.kind.value

    def is_assignable_to(self, target: 'FractalType') -> bool:
        if target.kind == TypeKind.ANY or self.kind == TypeKind.ANY:
            return True
        if self.kind == target.kind:
            if not target.subtypes:
                return True
            if len(self.subtypes) == len(target.subtypes):
                return all(s.is_assignable_to(t) for s, t in zip(self.subtypes, target.subtypes))
        return False

# Common type singletons
TYPE_INT = FractalType(TypeKind.INT)
TYPE_FLOAT = FractalType(TypeKind.FLOAT)
TYPE_STR = FractalType(TypeKind.STRING)
TYPE_BOOL = FractalType(TypeKind.BOOL)
TYPE_NONE = FractalType(TypeKind.NONE)
TYPE_ANY = FractalType(TypeKind.ANY)

class TypeCheckError(TypeError):
    pass

class TypeEnvironment:
    __slots__ = ("bindings", "parent")

    def __init__(self, parent: Optional['TypeEnvironment'] = None):
        self.bindings: Dict[str, FractalType] = {}
        self.parent = parent

    def lookup(self, name: str) -> FractalType:
        curr = self
        while curr is not None:
            if name in curr.bindings:
                return curr.bindings[name]
            curr = curr.parent
        return TYPE_ANY

    def bind(self, name: str, typ: FractalType) -> None:
        self.bindings[name] = typ

class TypeInferenceEngine:
    """
    Bidirectional Type Inference Engine for Fractal.
    Infers types without requiring developer type annotations.
    """
    __slots__ = ("global_env",)

    def __init__(self):
        self.global_env = TypeEnvironment()
        self._init_builtins()

    def _init_builtins(self):
        self.global_env.bind("print", FractalType(TypeKind.FUNCTION))
        self.global_env.bind("sqrt", FractalType(TypeKind.FUNCTION))
        self.global_env.bind("len", FractalType(TypeKind.FUNCTION))
        self.global_env.bind("str", FractalType(TypeKind.FUNCTION))
        self.global_env.bind("int", FractalType(TypeKind.FUNCTION))
        self.global_env.bind("float", FractalType(TypeKind.FUNCTION))

    def infer_program(self, program: ProgramNode) -> Dict[str, FractalType]:
        inferred = {}
        for stmt in program.statements:
            if isinstance(stmt, CellDefNode):
                t = self.infer_cell(stmt, self.global_env)
                self.global_env.bind(stmt.name, t)
                inferred[stmt.name] = t
            elif isinstance(stmt, AssignmentNode):
                t = self.infer_node(stmt.value, self.global_env)
                self.global_env.bind(stmt.target, t)
                inferred[stmt.target] = t
        return inferred

    def infer_cell(self, cell: CellDefNode, env: TypeEnvironment) -> FractalType:
        if cell.params is not None:
            # Parameterized callable cell
            cell_env = TypeEnvironment(parent=env)
            for p in cell.params:
                cell_env.bind(p, TYPE_ANY)
            ret_type = TYPE_NONE
            for stmt in cell.body:
                ret_type = self.infer_node(stmt, cell_env)
            return FractalType(TypeKind.FUNCTION, subtypes=[ret_type], cell_name=cell.name)
        else:
            # Module or Field cell
            if len(cell.body) == 1 and not isinstance(cell.body[0], CellDefNode):
                return self.infer_node(cell.body[0], env)
            return FractalType(TypeKind.CELL, cell_name=cell.name)

    def infer_node(self, node: ASTNode, env: TypeEnvironment) -> FractalType:
        if isinstance(node, LiteralNode):
            v = node.value
            if isinstance(v, bool): return TYPE_BOOL
            if isinstance(v, int): return TYPE_INT
            if isinstance(v, float): return TYPE_FLOAT
            if isinstance(v, str): return TYPE_STR
            if v is None: return TYPE_NONE
            return TYPE_ANY

        if isinstance(node, IdentifierNode):
            return env.lookup(node.name)

        if isinstance(node, ListNode):
            elem_types = [self.infer_node(e, env) for e in node.elements]
            elem_type = elem_types[0] if elem_types else TYPE_ANY
            return FractalType(TypeKind.LIST, subtypes=[elem_type])

        if isinstance(node, BinaryOpNode):
            l = self.infer_node(node.left, env)
            r = self.infer_node(node.right, env)
            if node.op in ("==", "!=", "<", ">", "<=", ">=", "and", "or"):
                return TYPE_BOOL
            if node.op in ("+", "-", "*", "/", "%", "^"):
                if l.kind == TypeKind.FLOAT or r.kind == TypeKind.FLOAT or node.op == "/":
                    return TYPE_FLOAT
                if l.kind == TypeKind.STRING or r.kind == TypeKind.STRING:
                    return TYPE_STR
                return TYPE_INT

        if isinstance(node, UnaryOpNode):
            if node.op == "not": return TYPE_BOOL
            return self.infer_node(node.expr, env)

        if isinstance(node, CallNode):
            # Function return type
            return TYPE_ANY

        if isinstance(node, CellDefNode):
            return self.infer_cell(node, env)

        return TYPE_ANY
