"""
Fractal Recursive Parser.
Parses the token stream into Fractal's uniform AST.
"""
from typing import List, Optional
from lexer import Token, TokenType, Lexer
from ast_nodes import (
    ASTNode, ProgramNode, CellDefNode, AssignmentNode, MemberAssignmentNode,
    PipelineNode, CallNode, MemberAccessNode, BinaryOpNode, UnaryOpNode,
    LiteralNode, IdentifierNode, ListNode, MapNode, IfNode, ForNode, WhileNode,
    UseNode, MatchCaseNode, MatchNode, SpawnNode, IndexAccessNode, IndexAssignmentNode
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def match(self, *expected_types: str) -> bool:
        if self.current().type in expected_types:
            self.pos += 1
            return True
        return False

    def expect(self, expected_type: str, msg: str = "") -> Token:
        token = self.current()
        if token.type != expected_type:
            detail = msg or f"Expected token {expected_type}, got {token.type} ({token.value})"
            raise SyntaxError(f"Line {token.line}, Col {token.column}: {detail}")
        self.pos += 1
        return token

    def parse(self) -> ProgramNode:
        statements: List[ASTNode] = []
        self._skip_newlines()
        while self.current().type != TokenType.EOF:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            self._skip_newlines()
        return ProgramNode(statements)

    def _skip_newlines(self):
        while self.current().type == TokenType.NEWLINE:
            self.pos += 1

    # --- Statements ---

    def statement(self) -> Optional[ASTNode]:
        self._skip_newlines()
        token = self.current()

        if token.type == TokenType.EOF:
            return None

        if token.type == TokenType.USE:
            self.pos += 1
            path_token = self.expect(TokenType.STRING, "Expected module path string after 'use'")
            alias = None
            if self.match(TokenType.AS):
                alias_token = self.expect(TokenType.IDENTIFIER, "Expected identifier after 'as'")
                alias = alias_token.value
            return UseNode(module_path=path_token.value, alias=alias)

        # Control flows
        if token.type == TokenType.IF:
            return self.if_statement()
        if token.type == TokenType.FOR:
            return self.for_statement()
        if token.type == TokenType.WHILE:
            return self.while_statement()
        if token.type == TokenType.MATCH:
            return self.match_statement()
        if token.type == TokenType.SPAWN:
            return self.spawn_statement()

        # Cell definitions:
        # 1. Identifier followed by ':' (inline or block cell without params)
        # 2. Identifier followed by '(' params ')' ':' (cell with params)
        if token.type == TokenType.IDENTIFIER:
            if self.peek().type == TokenType.COLON:
                # name: expr OR name: \n INDENT ...
                name = token.value
                self.pos += 2  # skip ID and ':'
                return self._parse_cell_body(name, None)
            
            if self.peek().type == TokenType.LPAREN:
                # Could be a function cell def `name(args): ...` OR a call statement `name(args)`
                # Lookahead to see if there's a matching ')' followed by ':'
                saved_pos = self.pos
                is_cell_def = False
                params = []
                self.pos += 2 # skip ID and '('
                
                # Check for parameter list
                can_be_params = True
                while self.current().type != TokenType.RPAREN and self.current().type != TokenType.EOF:
                    if self.current().type == TokenType.IDENTIFIER:
                        params.append(self.current().value)
                        self.pos += 1
                        if self.current().type == TokenType.COMMA:
                            self.pos += 1
                        elif self.current().type != TokenType.RPAREN:
                            can_be_params = False
                            break
                    else:
                        can_be_params = False
                        break

                if can_be_params and self.current().type == TokenType.RPAREN and self.peek().type == TokenType.COLON:
                    self.pos += 2 # skip ')' and ':'
                    return self._parse_cell_body(token.value, params)
                
                # Reset if not a cell def
                self.pos = saved_pos

        # Re-assignment: target = expr
        expr = self.expression()
        if self.current().type == TokenType.ASSIGN:
            self.pos += 1
            val = self.expression()
            if isinstance(expr, IdentifierNode):
                return AssignmentNode(expr.name, val)
            elif isinstance(expr, MemberAccessNode):
                return MemberAssignmentNode(expr.target, expr.member, val)
            elif isinstance(expr, IndexAccessNode):
                return IndexAssignmentNode(expr.target, expr.index, val)
            raise SyntaxError(f"Line {token.line}: Invalid assignment target")

        return expr

    def _parse_cell_body(self, name: str, params: Optional[List[str]]) -> CellDefNode:
        # Check if block (starts with NEWLINE and INDENT) or inline expression
        if self.current().type == TokenType.NEWLINE:
            self.pos += 1
            self.expect(TokenType.INDENT, "Expected indentation after ':' in cell definition")
            body_statements = []
            while self.current().type not in (TokenType.DEDENT, TokenType.EOF):
                self._skip_newlines()
                if self.current().type in (TokenType.DEDENT, TokenType.EOF):
                    break
                stmt = self.statement()
                if stmt:
                    body_statements.append(stmt)
                self._skip_newlines()
            self.expect(TokenType.DEDENT, "Expected dedent at the end of cell block")
            return CellDefNode(name=name, params=params, body=body_statements, is_inline=False)
        else:
            # Inline cell body
            expr = self.expression()
            return CellDefNode(name=name, params=params, body=[expr], is_inline=True)

    def if_statement(self) -> IfNode:
        self.expect(TokenType.IF)
        condition = self.expression()
        self.expect(TokenType.COLON, "Expected ':' after if condition")
        then_body = self._parse_block_or_expr()
        else_body = None
        self._skip_newlines()
        if self.match(TokenType.ELSE):
            self.expect(TokenType.COLON, "Expected ':' after else")
            else_body = self._parse_block_or_expr()
        return IfNode(condition=condition, then_body=then_body, else_body=else_body)

    def for_statement(self) -> ForNode:
        self.expect(TokenType.FOR)
        var_token = self.expect(TokenType.IDENTIFIER, "Expected loop variable name")
        self.expect(TokenType.IN, "Expected 'in' in for loop")
        iterable = self.expression()
        self.expect(TokenType.COLON, "Expected ':' after for statement")
        body = self._parse_block_or_expr()
        return ForNode(var_name=var_token.value, iterable=iterable, body=body)

    def while_statement(self) -> WhileNode:
        self.expect(TokenType.WHILE)
        condition = self.expression()
        self.expect(TokenType.COLON, "Expected ':' after while condition")
        body = self._parse_block_or_expr()
        return WhileNode(condition=condition, body=body)

    def match_statement(self) -> MatchNode:
        self.expect(TokenType.MATCH)
        subject = self.expression()
        self.expect(TokenType.COLON, "Expected ':' after match subject")
        self.expect(TokenType.NEWLINE, "Expected newline after match :")
        self.expect(TokenType.INDENT, "Expected indent for match cases")
        cases: List[MatchCaseNode] = []
        while self.current().type not in (TokenType.DEDENT, TokenType.EOF):
            self._skip_newlines()
            if self.current().type in (TokenType.DEDENT, TokenType.EOF):
                break
            pattern = self.expression()
            guard = None
            if self.match(TokenType.WHEN):
                guard = self.expression()
            self.expect(TokenType.COLON, "Expected ':' after match case pattern")
            body = self._parse_block_or_expr()
            cases.append(MatchCaseNode(pattern=pattern, guard=guard, body=body))
            self._skip_newlines()
        self.expect(TokenType.DEDENT, "Expected dedent at end of match block")
        return MatchNode(subject=subject, cases=cases)

    def spawn_statement(self) -> SpawnNode:
        self.expect(TokenType.SPAWN)
        self.expect(TokenType.COLON, "Expected ':' after spawn")
        body = self._parse_block_or_expr()
        return SpawnNode(body=body)

    def _parse_block_or_expr(self) -> List[ASTNode]:
        if self.match(TokenType.NEWLINE):
            self.expect(TokenType.INDENT)
            body = []
            while self.current().type not in (TokenType.DEDENT, TokenType.EOF):
                self._skip_newlines()
                if self.current().type in (TokenType.DEDENT, TokenType.EOF):
                    break
                stmt = self.statement()
                if stmt:
                    body.append(stmt)
                self._skip_newlines()
            self.expect(TokenType.DEDENT)
            return body
        else:
            return [self.expression()]

    # --- Expressions with Precedence ---

    def expression(self) -> ASTNode:
        return self.pipeline()

    def pipeline(self) -> ASTNode:
        left = self.logical_or()
        while self.match(TokenType.ARROW):
            right = self.logical_or()
            left = PipelineNode(left=left, right=right)
        return left

    def logical_or(self) -> ASTNode:
        left = self.logical_and()
        while self.match(TokenType.OR):
            right = self.logical_and()
            left = BinaryOpNode(left=left, op="or", right=right)
        return left

    def logical_and(self) -> ASTNode:
        left = self.comparison()
        while self.match(TokenType.AND):
            right = self.comparison()
            left = BinaryOpNode(left=left, op="and", right=right)
        return left

    def comparison(self) -> ASTNode:
        left = self.additive()
        ops = (TokenType.EQ_EQ, TokenType.BANG_EQ, TokenType.LT, TokenType.GT, TokenType.LT_EQ, TokenType.GT_EQ)
        while self.current().type in ops:
            op = self.current().type
            self.pos += 1
            right = self.additive()
            left = BinaryOpNode(left=left, op=op, right=right)
        return left

    def additive(self) -> ASTNode:
        left = self.multiplicative()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current().type
            self.pos += 1
            right = self.multiplicative()
            left = BinaryOpNode(left=left, op=op, right=right)
        return left

    def multiplicative(self) -> ASTNode:
        left = self.power()
        while self.current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.current().type
            self.pos += 1
            right = self.power()
            left = BinaryOpNode(left=left, op=op, right=right)
        return left

    def power(self) -> ASTNode:
        left = self.unary()
        if self.match(TokenType.POWER):
            right = self.power()  # Right-associative
            return BinaryOpNode(left=left, op="^", right=right)
        return left

    def unary(self) -> ASTNode:
        if self.current().type in (TokenType.MINUS, TokenType.NOT):
            op = self.current().type
            self.pos += 1
            return UnaryOpNode(op=op, expr=self.unary())
        return self.call_or_member()

    def call_or_member(self) -> ASTNode:
        expr = self.primary()
        while True:
            if self.match(TokenType.DOT):
                member_token = self.expect(TokenType.IDENTIFIER, "Expected member name after '.'")
                expr = MemberAccessNode(target=expr, member=member_token.value)
            elif self.match(TokenType.LPAREN):
                args = []
                if self.current().type != TokenType.RPAREN:
                    while True:
                        args.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallNode(callee=expr, args=args)
            elif self.match(TokenType.LBRACKET):
                index_expr = self.expression()
                self.expect(TokenType.RBRACKET, "Expected ']' after index expression")
                expr = IndexAccessNode(target=expr, index=index_expr)
            else:
                break
        return expr

    def primary(self) -> ASTNode:
        token = self.current()

        if token.type == TokenType.NUMBER:
            self.pos += 1
            return LiteralNode(token.value)

        if token.type == TokenType.STRING:
            self.pos += 1
            if "{" in token.value and "}" in token.value:
                return self._parse_interpolated_string(token.value)
            return LiteralNode(token.value)

        if token.type == TokenType.TRUE:
            self.pos += 1
            return LiteralNode(True)

        if token.type == TokenType.FALSE:
            self.pos += 1
            return LiteralNode(False)

        if token.type == TokenType.NONE:
            self.pos += 1
            return LiteralNode(None)

        if token.type == TokenType.IDENTIFIER:
            self.pos += 1
            return IdentifierNode(token.value)

        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        # List literal [a, b, c]
        if self.match(TokenType.LBRACKET):
            elements = []
            if self.current().type != TokenType.RBRACKET:
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACKET, "Expected ']' after list elements")
            return ListNode(elements)

        # Map literal {k: v, ...}
        if self.match(TokenType.LBRACE):
            pairs = []
            if self.current().type != TokenType.RBRACE:
                while True:
                    key = self.expression()
                    self.expect(TokenType.COLON, "Expected ':' after map key")
                    val = self.expression()
                    pairs.append((key, val))
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACE, "Expected '}' after map pairs")
            return MapNode(pairs)

        raise SyntaxError(f"Line {token.line}, Col {token.column}: Unexpected token {token.type} ({token.value})")

    def _parse_interpolated_string(self, text: str) -> ASTNode:
        import re
        tokens_or_literals = []
        pattern = re.compile(r"\{([^}]+)\}")
        last_idx = 0

        for match in pattern.finditer(text):
            start, end = match.span()
            if start > last_idx:
                literal_text = text[last_idx:start]
                tokens_or_literals.append(LiteralNode(literal_text))
            
            expr_str = match.group(1).strip()
            # Tokenize and parse sub-expression
            sub_lexer = Lexer(expr_str)
            sub_tokens = sub_lexer.tokenize()
            sub_parser = Parser(sub_tokens)
            expr_node = sub_parser.expression()
            
            # Wrap in str(expr) call
            str_call = CallNode(callee=IdentifierNode("str"), args=[expr_node])
            tokens_or_literals.append(str_call)
            last_idx = end

        if last_idx < len(text):
            tokens_or_literals.append(LiteralNode(text[last_idx:]))

        if not tokens_or_literals:
            return LiteralNode("")

        # Fold into binary additions: part1 + part2 + ...
        res = tokens_or_literals[0]
        for next_part in tokens_or_literals[1:]:
            res = BinaryOpNode(left=res, op="+", right=next_part)
        return res
