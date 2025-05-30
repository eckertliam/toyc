from typing import Iterator
from tokens import Token, TokenKind
from toycast import Block, FnDecl, Program

# TODO: rewrite to collect errors and report them at the end


class Parser:
    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens: Iterator[Token] = tokens
        self.previous: Token = next(self.tokens)
        self.current: Token = next(self.tokens)

    def advance(self) -> Token:
        self.previous = self.current
        self.current = next(self.tokens)
        return self.previous

    def expect(self, kind: TokenKind, message: str) -> Token:
        if self.current.kind == kind:
            token = self.current
            self.advance()
            return token
        raise SyntaxError(
            f"[Line {self.current.line}] {message}, found {self.current.lexeme}"
        )

    def parse_program(self) -> Program:
        functions = []
        while self.current.kind != TokenKind.EOF:
            fn = self.parse_function()
            functions.append(fn)
        return Program(line=1, functions=functions)

    def parse_function(self):
        # Assume function declaration looks like: fn name(param: type, ...) -> type { ... }
        self.expect(TokenKind.FN, "Expected 'fn' at start of function declaration")
        name_token = self.expect(TokenKind.IDENT, "Expected function name")
        self.expect(TokenKind.LPAREN, "Expected '(' after function name")
        params = []
        if self.current.kind != TokenKind.RPAREN:
            while True:
                param_name = self.expect(TokenKind.IDENT, "Expected parameter name")
                self.expect(TokenKind.COLON, "Expected ':' after parameter name")
                param_type = self.expect(TokenKind.IDENT, "Expected parameter type")
                params.append((param_name.lexeme, param_type.lexeme))
                if not self.match(TokenKind.COMMA):
                    break
        self.expect(TokenKind.RPAREN, "Expected ')' after parameters")
        self.expect(TokenKind.COLON, "Expected ':' before return type")
        return_type_token = self.expect(TokenKind.IDENT, "Expected return type")
        body = self.parse_block()
        return FnDecl(
            line=name_token.line,
            name=name_token.lexeme,
            params=params,
            return_type=return_type_token.lexeme,
            body=body,
        )

    def parse_block(self):
        self.expect(TokenKind.LBRACE, "Expected '{' to start block")
        statements = []
        while not self.current.kind == TokenKind.RBRACE:
            stmt = self.parse_stmt()
            statements.append(stmt)
            if self.match(TokenKind.EOF):
                break
        self.expect(TokenKind.RBRACE, "Expected '}' to end block")
        return Block(line=self.previous.line, statements=statements)

    def parse_stmt(self):
        if self.match(TokenKind.LET):
            return self.parse_var_decl()
        elif self.match(TokenKind.IF):
            return self.parse_if_stmt()
        elif self.match(TokenKind.GOTO):
            return self.parse_goto_stmt()
        elif self.match(TokenKind.IDENT) and self.current.kind == TokenKind.COLON:
            return self.parse_label_stmt()
        elif self.match(TokenKind.RETURN):
            return self.parse_return_stmt()
        else:
            raise SyntaxError(
                f"[Line {self.current.line}] Expected statement, found {self.current.lexeme}"
            )

    # Placeholder methods for now
    def parse_var_decl(self):
        # TODO: Implement this
        raise NotImplementedError

    def parse_fn_decl(self):
        # TODO: Implement this
        raise NotImplementedError

    def parse_if_stmt(self):
        # TODO: Implement this
        raise NotImplementedError

    def parse_goto_stmt(self):
        # TODO: Implement this
        raise NotImplementedError

    def parse_label_stmt(self):
        # TODO: Implement this
        raise NotImplementedError

    def parse_return_stmt(self):
        # TODO: Implement this
        raise NotImplementedError

    def match(self, *kinds: TokenKind) -> bool:
        for kind in kinds:
            if self.current.kind == kind:
                return True
        return False
