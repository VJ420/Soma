"""
Soma bytecode compiler.
Translates a Soma AST into chunks for the Soma virtual machine.
"""
from typing import List, Optional
from bytecode import OpCode, BytecodeChunk
from ast_nodes import (
    ASTNode, ProgramNode, CellDefNode, AssignmentNode, MemberAssignmentNode,
    PipelineNode, CallNode, MemberAccessNode, BinaryOpNode, UnaryOpNode,
    LiteralNode, IdentifierNode, ListNode, MapNode, IfNode, ForNode, WhileNode,
    IndexAccessNode, IndexAssignmentNode, MatchNode
)


class CompileError(NotImplementedError):
    """Raised when a Soma construct cannot run on the bytecode engine."""

class Compiler:
    def __init__(self):
        self.chunk = BytecodeChunk(instructions=[], constants=[], names=[])

    def compile(self, program: ProgramNode) -> BytecodeChunk:
        for stmt in program.statements:
            self._compile_node(stmt)
        self.chunk.add_instruction(OpCode.HALT)
        return self.chunk

    def _compile_node(self, node: ASTNode):
        if isinstance(node, LiteralNode):
            c_idx = self.chunk.add_constant(node.value)
            self.chunk.add_instruction(OpCode.LOAD_CONST, c_idx)

        elif isinstance(node, IdentifierNode):
            n_idx = self.chunk.add_name(node.name)
            self.chunk.add_instruction(OpCode.LOAD_NAME, n_idx)

        elif isinstance(node, ListNode):
            for elem in node.elements:
                self._compile_node(elem)
            self.chunk.add_instruction(OpCode.BUILD_LIST, len(node.elements))

        elif isinstance(node, MapNode):
            for k, v in node.pairs:
                self._compile_node(k)
                self._compile_node(v)
            self.chunk.add_instruction(OpCode.BUILD_MAP, len(node.pairs))

        elif isinstance(node, AssignmentNode):
            self._compile_node(node.value)
            n_idx = self.chunk.add_name(node.target)
            self.chunk.add_instruction(OpCode.STORE_NAME, n_idx)

        elif isinstance(node, MemberAssignmentNode):
            self._compile_node(node.target)
            self._compile_node(node.value)
            n_idx = self.chunk.add_name(node.member)
            self.chunk.add_instruction(OpCode.SET_ATTR, n_idx)

        elif isinstance(node, MemberAccessNode):
            self._compile_node(node.target)
            n_idx = self.chunk.add_name(node.member)
            self.chunk.add_instruction(OpCode.GET_ATTR, n_idx)

        elif isinstance(node, IndexAccessNode):
            self._compile_node(node.target)
            self._compile_node(node.index)
            self.chunk.add_instruction(OpCode.GET_INDEX)

        elif isinstance(node, IndexAssignmentNode):
            self._compile_node(node.target)
            self._compile_node(node.index)
            self._compile_node(node.value)
            self.chunk.add_instruction(OpCode.SET_INDEX)

        elif isinstance(node, BinaryOpNode):
            if node.op == "and":
                self._compile_logic(node, jump_when_true=False)
                return
            if node.op == "or":
                self._compile_logic(node, jump_when_true=True)
                return
            self._compile_node(node.left)
            self._compile_node(node.right)
            op_map = {
                "+": OpCode.ADD,
                "-": OpCode.SUB,
                "*": OpCode.MUL,
                "/": OpCode.DIV,
                "%": OpCode.MOD,
                "^": OpCode.POW,
                "==": OpCode.EQ,
                "!=": OpCode.NEQ,
                "<": OpCode.LT,
                ">": OpCode.GT,
                "<=": OpCode.LTE,
                ">=": OpCode.GTE,
            }
            if node.op in op_map:
                self.chunk.add_instruction(op_map[node.op])
            else:
                raise CompileError(f"Binary operator {node.op} is not implemented in the Soma VM")

        elif isinstance(node, UnaryOpNode):
            if node.op == "-":
                c_idx = self.chunk.add_constant(0)
                self.chunk.add_instruction(OpCode.LOAD_CONST, c_idx)
                self._compile_node(node.expr)
                self.chunk.add_instruction(OpCode.SUB)
            elif node.op == "not":
                self._compile_node(node.expr)
                self.chunk.add_instruction(OpCode.NOT)

        elif isinstance(node, CallNode):
            self._compile_node(node.callee)
            for arg in node.args:
                self._compile_node(arg)
            self.chunk.add_instruction(OpCode.CALL_CELL, len(node.args))

        elif isinstance(node, PipelineNode):
            # Left to right: expr -> target
            if isinstance(node.right, CallNode):
                # e.g. expr -> filter(is_even)
                self._compile_node(node.right.callee)
                self._compile_node(node.left)
                for arg in node.right.args:
                    self._compile_node(arg)
                self.chunk.add_instruction(OpCode.CALL_CELL, 1 + len(node.right.args))
            else:
                self._compile_node(node.right)
                self._compile_node(node.left)
                self.chunk.add_instruction(OpCode.CALL_CELL, 1)

        elif isinstance(node, IfNode):
            self._compile_node(node.condition)
            jump_false_idx = self.chunk.add_instruction(OpCode.JUMP_IF_FALSE, 0)
            
            for stmt in node.then_body:
                self._compile_node(stmt)

            if node.else_body:
                jump_end_idx = self.chunk.add_instruction(OpCode.JUMP, 0)
                # Patch jump_false to point to start of else body
                self.chunk.instructions[jump_false_idx].arg = len(self.chunk.instructions)
                for stmt in node.else_body:
                    self._compile_node(stmt)
                # Patch jump_end to point past else body
                self.chunk.instructions[jump_end_idx].arg = len(self.chunk.instructions)
            else:
                self.chunk.instructions[jump_false_idx].arg = len(self.chunk.instructions)

        elif isinstance(node, WhileNode):
            loop_start = len(self.chunk.instructions)
            self._compile_node(node.condition)
            jump_exit = self.chunk.add_instruction(OpCode.JUMP_IF_FALSE, 0)
            
            for stmt in node.body:
                self._compile_node(stmt)
            
            self.chunk.add_instruction(OpCode.JUMP, loop_start)
            self.chunk.instructions[jump_exit].arg = len(self.chunk.instructions)

        elif isinstance(node, ForNode):
            # For loop compilation: iterate through list
            self._compile_node(node.iterable)
            # Create sub-environment or standard loop
            iter_name = f"__iter_{node.var_name}"
            i_name = f"__i_{node.var_name}"
            
            # Save iterable
            self.chunk.add_instruction(OpCode.STORE_NAME, self.chunk.add_name(iter_name))
            # i = 0
            self.chunk.add_instruction(OpCode.LOAD_CONST, self.chunk.add_constant(0))
            self.chunk.add_instruction(OpCode.STORE_NAME, self.chunk.add_name(i_name))

            loop_start = len(self.chunk.instructions)
            # i < len(iter)
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(i_name))
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name("len"))
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(iter_name))
            self.chunk.add_instruction(OpCode.CALL_CELL, 1)
            self.chunk.add_instruction(OpCode.LT)

            jump_exit = self.chunk.add_instruction(OpCode.JUMP_IF_FALSE, 0)

            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(iter_name))
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(i_name))
            self.chunk.add_instruction(OpCode.GET_INDEX)
            self.chunk.add_instruction(OpCode.STORE_NAME, self.chunk.add_name(node.var_name))

            for stmt in node.body:
                self._compile_node(stmt)

            # i = i + 1
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(i_name))
            self.chunk.add_instruction(OpCode.LOAD_CONST, self.chunk.add_constant(1))
            self.chunk.add_instruction(OpCode.ADD)
            self.chunk.add_instruction(OpCode.STORE_NAME, self.chunk.add_name(i_name))

            self.chunk.add_instruction(OpCode.JUMP, loop_start)
            self.chunk.instructions[jump_exit].arg = len(self.chunk.instructions)

        elif isinstance(node, CellDefNode):
            # Compile nested Cell into its own BytecodeChunk!
            sub_compiler = Compiler()
            for stmt in node.body:
                sub_compiler._compile_node(stmt)
            sub_compiler.chunk.add_instruction(OpCode.RETURN)

            returns_instance = (
                node.params is not None
                and bool(node.body)
                and any(isinstance(stmt, CellDefNode) for stmt in node.body)
                and isinstance(node.body[-1], CellDefNode)
            )
            cell_meta = {
                "name": node.name,
                "params": node.params,
                "chunk": sub_compiler.chunk,
                "returns_instance": returns_instance,
            }
            c_idx = self.chunk.add_constant(cell_meta)
            self.chunk.add_instruction(OpCode.MAKE_CELL, c_idx)
            n_idx = self.chunk.add_name(node.name)
            self.chunk.add_instruction(OpCode.STORE_NAME, n_idx)

        elif isinstance(node, MatchNode):
            self._compile_match(node)

        else:
            raise CompileError(
                f"{type(node).__name__} is not available on the Soma VM. "
                "Run the file with `soma run` or `--engine interpreter`."
            )

    def _compile_logic(self, node: BinaryOpNode, jump_when_true: bool) -> None:
        self._compile_node(node.left)
        self.chunk.add_instruction(OpCode.DUP)
        opcode = OpCode.JUMP_IF_TRUE if jump_when_true else OpCode.JUMP_IF_FALSE
        jump = self.chunk.add_instruction(opcode, 0)
        self.chunk.add_instruction(OpCode.POP)
        self._compile_node(node.right)
        self.chunk.instructions[jump].arg = len(self.chunk.instructions)

    def _compile_match(self, node: MatchNode) -> None:
        slot = f"__match_{id(node)}"
        self._compile_node(node.subject)
        self.chunk.add_instruction(OpCode.STORE_NAME, self.chunk.add_name(slot))
        end_jumps = []
        for case in node.cases:
            compare_jump = None
            if isinstance(case.pattern, IdentifierNode) and case.pattern.name == "_":
                pass
            elif isinstance(case.pattern, IdentifierNode):
                self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(slot))
                self.chunk.add_instruction(OpCode.STORE_NAME, self.chunk.add_name(case.pattern.name))
            else:
                self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(slot))
                self._compile_node(case.pattern)
                self.chunk.add_instruction(OpCode.EQ)
                compare_jump = self.chunk.add_instruction(OpCode.JUMP_IF_FALSE, 0)
            guard_jump = None
            if case.guard is not None:
                self._compile_node(case.guard)
                guard_jump = self.chunk.add_instruction(OpCode.JUMP_IF_FALSE, 0)
            for stmt in case.body:
                self._compile_node(stmt)
            end_jumps.append(self.chunk.add_instruction(OpCode.JUMP, 0))
            landing = len(self.chunk.instructions)
            if compare_jump is not None:
                self.chunk.instructions[compare_jump].arg = landing
            if guard_jump is not None:
                self.chunk.instructions[guard_jump].arg = landing
        self.chunk.add_instruction(OpCode.LOAD_CONST, self.chunk.add_constant(None))
        done = len(self.chunk.instructions)
        for jump in end_jumps:
            self.chunk.instructions[jump].arg = done
