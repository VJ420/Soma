"""
Fractal Lexer.
Tokenizes Fractal source code with indentation sensitivity (INDENT / DEDENT).
"""
import re
from typing import List, Optional, Any

class TokenType:
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    
    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    POWER = "^"
    PERCENT = "%"
    
    EQ_EQ = "=="
    BANG_EQ = "!="
    LT = "<"
    GT = ">"
    LT_EQ = "<="
    GT_EQ = ">="
    
    ARROW = "->"
    COLON = ":"
    DOT = "."
    COMMA = ","
    ASSIGN = "="
    
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"
    
    # Keywords
    IF = "if"
    ELSE = "else"
    FOR = "for"
    IN = "in"
    WHILE = "while"
    TRUE = "true"
    FALSE = "false"
    NONE = "none"
    AND = "and"
    OR = "or"
    NOT = "not"
    USE = "use"
    AS = "as"
    MATCH = "match"
    WHEN = "when"
    SPAWN = "spawn"
    
    # Structure
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"

KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "while": TokenType.WHILE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "none": TokenType.NONE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "use": TokenType.USE,
    "as": TokenType.AS,
    "match": TokenType.MATCH,
    "when": TokenType.WHEN,
    "spawn": TokenType.SPAWN,
}

class Token:
    def __init__(self, type_: str, value: Any = None, line: int = 1, column: int = 1):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        val = f", {repr(self.value)}" if self.value is not None else ""
        return f"Token({self.type}{val}, L{self.line}:C{self.column})"

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        lines = self.source.splitlines(keepends=True)
        
        for line_idx, line in enumerate(lines, start=1):
            self.line = line_idx
            self.column = 1
            stripped = line.strip()
            
            # Ignore empty lines or pure comment lines
            if not stripped or stripped.startswith("#"):
                continue

            # Calculate indentation for non-empty lines
            leading_spaces = len(line) - len(line.lstrip(" "))
            current_indent = self.indent_stack[-1]

            if leading_spaces > current_indent:
                self.indent_stack.append(leading_spaces)
                self.tokens.append(Token(TokenType.INDENT, leading_spaces, self.line, 1))
            elif leading_spaces < current_indent:
                while self.indent_stack and self.indent_stack[-1] > leading_spaces:
                    self.indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, leading_spaces, self.line, 1))
                if self.indent_stack[-1] != leading_spaces:
                    raise SyntaxError(f"Line {self.line}: Inconsistent indentation levels")

            # Tokenize contents of the line
            self._tokenize_line(line[leading_spaces:], offset=leading_spaces + 1)
            self.tokens.append(Token(TokenType.NEWLINE, line=self.line, column=len(line)))

        # Close remaining indents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line, self.column))

        self.tokens.append(Token(TokenType.EOF, line=self.line, column=self.column))
        return self.tokens

    def _tokenize_line(self, line: str, offset: int):
        i = 0
        n = len(line)

        while i < n:
            ch = line[i]
            col = offset + i

            # Whitespace
            if ch in " \t\r\n":
                i += 1
                continue

            # Comments
            if ch == "#":
                break

            # 2-character operators
            two = line[i:i+2]
            if two == "->":
                self.tokens.append(Token(TokenType.ARROW, "->", self.line, col))
                i += 2
                continue
            elif two == "==":
                self.tokens.append(Token(TokenType.EQ_EQ, "==", self.line, col))
                i += 2
                continue
            elif two == "!=":
                self.tokens.append(Token(TokenType.BANG_EQ, "!=", self.line, col))
                i += 2
                continue
            elif two == "<=":
                self.tokens.append(Token(TokenType.LT_EQ, "<=", self.line, col))
                i += 2
                continue
            elif two == ">=":
                self.tokens.append(Token(TokenType.GT_EQ, ">=", self.line, col))
                i += 2
                continue

            # 1-character operators & delimiters
            single_map = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "^": TokenType.POWER,
                "%": TokenType.PERCENT,
                "<": TokenType.LT,
                ">": TokenType.GT,
                ":": TokenType.COLON,
                ".": TokenType.DOT,
                ",": TokenType.COMMA,
                "=": TokenType.ASSIGN,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
            }
            if ch in single_map:
                self.tokens.append(Token(single_map[ch], ch, self.line, col))
                i += 1
                continue

            # Strings
            if ch in ('"', "'"):
                quote_char = ch
                start_col = col
                i += 1
                str_val = []
                while i < n and line[i] != quote_char:
                    if line[i] == "\\" and i + 1 < n:
                        i += 1
                        esc = line[i]
                        if esc == 'n': str_val.append('\n')
                        elif esc == 't': str_val.append('\t')
                        elif esc == '\\': str_val.append('\\')
                        elif esc == quote_char: str_val.append(quote_char)
                        else: str_val.append(esc)
                    else:
                        str_val.append(line[i])
                    i += 1
                if i < n and line[i] == quote_char:
                    i += 1
                    self.tokens.append(Token(TokenType.STRING, "".join(str_val), self.line, start_col))
                else:
                    raise SyntaxError(f"Line {self.line}: Unterminated string literal")
                continue

            # Numbers
            if ch.isdigit():
                num_start = i
                has_dot = False
                while i < n and (line[i].isdigit() or (line[i] == '.' and not has_dot and i+1 < n and line[i+1].isdigit())):
                    if line[i] == '.':
                        has_dot = True
                    i += 1
                raw_num = line[num_start:i]
                val = float(raw_num) if has_dot else int(raw_num)
                self.tokens.append(Token(TokenType.NUMBER, val, self.line, col))
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == "_":
                id_start = i
                while i < n and (line[i].isalnum() or line[i] == "_"):
                    i += 1
                id_str = line[id_start:i]
                token_type = KEYWORDS.get(id_str, TokenType.IDENTIFIER)
                val = None if token_type in KEYWORDS else id_str
                self.tokens.append(Token(token_type, val, self.line, col))
                continue

            raise SyntaxError(f"Line {self.line}: Unexpected character '{ch}' at column {col}")
