"""
Fractal Bytecode Compiler.
Translates AST into high-speed BytecodeChunks for the Fractal Virtual Machine.
"""
from typing import List, Optional
from bytecode import OpCode, BytecodeChunk
from ast_nodes import (
    ASTNode, ProgramNode, CellDefNode, AssignmentNode, MemberAssignmentNode,
    PipelineNode, CallNode, MemberAccessNode, BinaryOpNode, UnaryOpNode,
    LiteralNode, IdentifierNode, ListNode, MapNode, IfNode, ForNode, WhileNode
)

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

        elif isinstance(node, BinaryOpNode):
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
                raise NotImplementedError(f"Binary operator {node.op} not implemented in compiler")

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

            # var = iter[i]
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(iter_name))
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(i_name))
            # Builtin indexing via GET_ATTR or call
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name("__get_index"))
            # For VM list access
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(iter_name))
            self.chunk.add_instruction(OpCode.LOAD_NAME, self.chunk.add_name(i_name))
            self.chunk.add_instruction(OpCode.CALL_CELL, 2)
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

            cell_meta = {
                "name": node.name,
                "params": node.params,
                "chunk": sub_compiler.chunk
            }
            c_idx = self.chunk.add_constant(cell_meta)
            self.chunk.add_instruction(OpCode.MAKE_CELL, c_idx)
            n_idx = self.chunk.add_name(node.name)
            self.chunk.add_instruction(OpCode.STORE_NAME, n_idx)
