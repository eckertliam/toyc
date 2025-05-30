from tokens import Token, TokenKind
from typing import Iterator


# a simple greedy scanner
class Scanner:
    def __init__(self, source: str) -> None:
        self.source = source
        self.line = 1
        self.start = 0
        self.current = 0

    def __iter__(self) -> Iterator[Token]:
        return self.tokenize()

    def tokenize(self) -> Iterator[Token]:
        while not self.is_at_end():
            yield self.scan_token()
        yield Token(TokenKind.EOF, "", self.line)

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
        return char

    def make_token(self, kind: TokenKind) -> Token:
        lexeme = self.source[self.start : self.current]
        return Token(kind, lexeme, self.line)

    def branch_token(
        self, if_char: str, then_kind: TokenKind, else_kind: TokenKind
    ) -> Token:
        if self.peek() == if_char:
            self.advance()
            return self.make_token(then_kind)
        else:
            return self.make_token(else_kind)

    def error_token(self, message: str) -> Token:
        return Token(TokenKind.ERROR, message, self.line)

    def scan_token(self) -> Token:
        self.start = self.current
        c = self.advance()

        if c == "(":
            return self.make_token(TokenKind.LPAREN)
        elif c == ")":
            return self.make_token(TokenKind.RPAREN)
        elif c == "{":
            return self.make_token(TokenKind.LBRACE)
        elif c == "}":
            return self.make_token(TokenKind.RBRACE)
        elif c == ";":
            return self.make_token(TokenKind.SEMICOLON)
        elif c == ":":
            return self.make_token(TokenKind.COLON)
        elif c == "+":
            return self.make_token(TokenKind.PLUS)
        elif c == "-":
            return self.make_token(TokenKind.MINUS)
        elif c == "*":
            return self.make_token(TokenKind.STAR)
        elif c == "/":
            return self.make_token(TokenKind.SLASH)
        elif c == "%":
            return self.make_token(TokenKind.MOD)
        elif c == "=":
            return self.branch_token("=", TokenKind.EQEQ, TokenKind.EQ)
        elif c == "!":
            return self.branch_token("=", TokenKind.BANGEQ, TokenKind.BANG)
        elif c == "<":
            return self.branch_token("=", TokenKind.LTEQ, TokenKind.LT)
        elif c == ">":
            return self.branch_token("=", TokenKind.GTEQ, TokenKind.GT)
        elif c == ",":
            return self.make_token(TokenKind.COMMA)
        elif c == "&":
            if self.peek() == "&":
                self.advance()
                return self.make_token(TokenKind.AMPAMP)
            else:
                return self.error_token("Expected `&&`")
        elif c == "|":
            if self.peek() == "|":
                self.advance()
                return self.make_token(TokenKind.PIPEPIPE)
            else:
                return self.error_token("Expected `||`")
        elif c.isalpha() or c == "_":
            return self.identifier()
        elif c.isdigit():
            return self.number()
        elif c in ["\n", " "]:
            return self.scan_token()
        else:
            return self.error_token(f"Unexpected character: {c}")

    def identifier(self) -> Token:
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()

        # check for keywords
        kind = {
            "if": TokenKind.IF,
            "else": TokenKind.ELSE,
            "goto": TokenKind.GOTO,
            "label": TokenKind.LABEL,
            "return": TokenKind.RETURN,
            "let": TokenKind.LET,
            "const": TokenKind.CONST,
            "fn": TokenKind.FN,
            "true": TokenKind.TRUE,
            "false": TokenKind.FALSE,
        }.get(self.source[self.start : self.current], TokenKind.IDENT)

        return self.make_token(kind)

    def number(self) -> Token:
        def consume_digits() -> None:
            while self.peek().isdigit():
                self.advance()

        consume_digits()

        if self.peek() == ".":
            self.advance()
            consume_digits()

        return self.make_token(TokenKind.NUMBER)
