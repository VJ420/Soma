"""
Production-Grade Abstract Syntax Tree for Fractal.
Optimized with __slots__ to eliminate dict overhead and guarantee O(1) attribute access.
Strictly typed, memory-efficient, and immutable wherever appropriate.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

class ASTNode:
    __slots__ = ()

@dataclass(slots=True, frozen=True)
class LiteralNode(ASTNode):
    value: Any

@dataclass(slots=True, frozen=True)
class IdentifierNode(ASTNode):
    name: str

@dataclass(slots=True, frozen=True)
class ListNode(ASTNode):
    elements: List[ASTNode]

@dataclass(slots=True, frozen=True)
class MapNode(ASTNode):
    pairs: List[Tuple[ASTNode, ASTNode]]

@dataclass(slots=True)
class CellDefNode(ASTNode):
    """
    The Universal Fractal Construct.
    - params is None: Field / Module / Namespace
    - params is list: Parameterized Callable Cell (Function, Constructor, Method)
    """
    name: str
    params: Optional[List[str]] = None
    body: List[ASTNode] = field(default_factory=list)
    is_inline: bool = False

@dataclass(slots=True, frozen=True)
class AssignmentNode(ASTNode):
    target: str
    value: ASTNode

@dataclass(slots=True, frozen=True)
class MemberAssignmentNode(ASTNode):
    target: ASTNode
    member: str
    value: ASTNode

@dataclass(slots=True, frozen=True)
class IndexAccessNode(ASTNode):
    target: ASTNode
    index: ASTNode

@dataclass(slots=True, frozen=True)
class IndexAssignmentNode(ASTNode):
    target: ASTNode
    index: ASTNode
    value: ASTNode

@dataclass(slots=True, frozen=True)
class PipelineNode(ASTNode):
    """Left-to-right pipe: expr -> target"""
    left: ASTNode
    right: ASTNode

@dataclass(slots=True, frozen=True)
class CallNode(ASTNode):
    callee: ASTNode
    args: List[ASTNode]

@dataclass(slots=True, frozen=True)
class MemberAccessNode(ASTNode):
    target: ASTNode
    member: str

@dataclass(slots=True, frozen=True)
class BinaryOpNode(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass(slots=True, frozen=True)
class UnaryOpNode(ASTNode):
    op: str
    expr: ASTNode

@dataclass(slots=True, frozen=True)
class IfNode(ASTNode):
    condition: ASTNode
    then_body: List[ASTNode]
    else_body: Optional[List[ASTNode]] = None

@dataclass(slots=True, frozen=True)
class ForNode(ASTNode):
    var_name: str
    iterable: ASTNode
    body: List[ASTNode]

@dataclass(slots=True, frozen=True)
class WhileNode(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass(slots=True, frozen=True)
class UseNode(ASTNode):
    module_path: str
    alias: Optional[str] = None

@dataclass(slots=True, frozen=True)
class MatchCaseNode(ASTNode):
    pattern: ASTNode
    guard: Optional[ASTNode]
    body: List[ASTNode]

@dataclass(slots=True, frozen=True)
class MatchNode(ASTNode):
    subject: ASTNode
    cases: List[MatchCaseNode]

@dataclass(slots=True, frozen=True)
class SpawnNode(ASTNode):
    body: List[ASTNode]

@dataclass(slots=True, frozen=True)
class ProgramNode(ASTNode):
    statements: List[ASTNode]
