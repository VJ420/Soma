"""
Fractal Bytecode Instruction Set and OpCodes.
Production-grade Bytecode Virtual Machine Architecture.
"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, List, Optional

class OpCode(Enum):
    # Stack manipulation
    LOAD_CONST = auto()
    LOAD_NAME = auto()
    STORE_NAME = auto()
    POP = auto()
    DUP = auto()

    # Binary Arithmetic & Logic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    POW = auto()
    
    # Comparisons
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Flow Control
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()

    # Data Structures
    BUILD_LIST = auto()
    BUILD_MAP = auto()

    # Attribute & Member Access
    GET_ATTR = auto()
    SET_ATTR = auto()

    # Cell / Function / Invocation
    MAKE_CELL = auto()
    CALL_CELL = auto()
    RETURN = auto()

    # Module System
    IMPORT_MODULE = auto()

    # Halting
    HALT = auto()

@dataclass
class Instruction:
    opcode: OpCode
    arg: Any = None
    line: int = 1

    def __repr__(self):
        arg_str = f" {repr(self.arg)}" if self.arg is not None else ""
        return f"{self.opcode.name:<18}{arg_str}"

@dataclass
class BytecodeChunk:
    instructions: List[Instruction]
    constants: List[Any]
    names: List[str]

    def add_instruction(self, opcode: OpCode, arg: Any = None, line: int = 1) -> int:
        idx = len(self.instructions)
        self.instructions.append(Instruction(opcode, arg, line))
        return idx

    def add_constant(self, value: Any) -> int:
        for idx, const in enumerate(self.constants):
            if const == value and type(const) is type(value):
                return idx
        self.constants.append(value)
        return len(self.constants) - 1

    def add_name(self, name: str) -> int:
        if name in self.names:
            return self.names.index(name)
        self.names.append(name)
        return len(self.names) - 1

    def disassemble(self, title: str = "CHUNK") -> str:
        lines = [f"=== DISASSEMBLY: {title} ==="]
        lines.append(f"Constants: {self.constants}")
        lines.append(f"Names:     {self.names}")
        lines.append("-" * 40)
        for offset, inst in enumerate(self.instructions):
            lines.append(f"{offset:04d}  {inst}")
        return "\n".join(lines)
