from typing import Iterator, List
from tokens import Token, TokenKind
from toycast import (
    Assign,
    Body,
    BoolLit,
    Expr,
    ExprStmt,
    FloatLit,
    FnDecl,
    Goto,
    If,
    Label,
    Param,
    Program,
    Return,
    Stmt,
    Unary,
    VarDecl,
)
from toycast import IntLit, Ident, Binary, Call

# TODO: support for boolean literals


class ParseError(Exception):
    def __init__(self, message: str, line: int, lexeme: str) -> None:
        self.message = message
        self.line = line
        self.lexeme = lexeme

    def __str__(self) -> str:
        return f"[Line {self.line}] {self.message}, found {self.lexeme}"


class Parser:
    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens: Iterator[Token] = tokens
        self.previous: Token = Token(TokenKind.EOF, "", 0)
        self.current: Token = next(self.tokens)
        self.errors: List[ParseError] = []

        self.prefix_parse_fns = {
            TokenKind.NUMBER: self.parse_number,
            TokenKind.IDENT: self.parse_identifier,
            TokenKind.TRUE: self.parse_bool,
            TokenKind.FALSE: self.parse_bool,
            TokenKind.LPAREN: self.parse_grouping,
            TokenKind.BANG: self.parse_unary,
            TokenKind.MINUS: self.parse_unary,
        }

        self.infix_parse_fns = {
            TokenKind.PLUS: self.parse_infix_binary,
            TokenKind.MINUS: self.parse_infix_binary,
            TokenKind.STAR: self.parse_infix_binary,
            TokenKind.SLASH: self.parse_infix_binary,
            TokenKind.MOD: self.parse_infix_binary,
            TokenKind.LPAREN: self.parse_call,
            TokenKind.EQ: self.parse_infix_binary,
            TokenKind.PIPEPIPE: self.parse_infix_binary,
            TokenKind.AMPAMP: self.parse_infix_binary,
            TokenKind.EQEQ: self.parse_infix_binary,
            TokenKind.BANGEQ: self.parse_infix_binary,
            TokenKind.LT: self.parse_infix_binary,
            TokenKind.LTEQ: self.parse_infix_binary,
            TokenKind.GT: self.parse_infix_binary,
            TokenKind.GTEQ: self.parse_infix_binary,
        }

        self.precedences = {
            TokenKind.EQ: 1,
            TokenKind.PIPEPIPE: 2,
            TokenKind.AMPAMP: 3,
            TokenKind.EQEQ: 4,
            TokenKind.BANGEQ: 4,
            TokenKind.LT: 5,
            TokenKind.LTEQ: 5,
            TokenKind.GT: 5,
            TokenKind.GTEQ: 5,
            TokenKind.PLUS: 6,
            TokenKind.MINUS: 6,
            TokenKind.STAR: 7,
            TokenKind.SLASH: 7,
            TokenKind.MOD: 7,
            TokenKind.LPAREN: 8,
        }

    def synchronize(self, *kinds: TokenKind) -> None:
        while not self.match(*kinds):
            try:
                self.advance()
            except StopIteration:
                break

    def advance(self) -> Token:
        self.previous = self.current
        self.current = next(self.tokens)
        return self.previous

    def expect(self, kind: TokenKind, message: str) -> Token:
        if self.current.kind == kind:
            token = self.current
            self.advance()
            return token
        else:
            raise ParseError(message, self.current.line, self.current.lexeme)

    def match(self, *kinds: TokenKind) -> bool:
        for kind in kinds:
            if self.current.kind == kind:
                return True
        return False

    def match_consume(self, *kinds: TokenKind) -> bool:
        if self.match(*kinds):
            self.advance()
            return True
        return False

    def parse_program(self, name: str) -> Program:
        functions = []
        while self.current.kind != TokenKind.EOF:
            try:
                fn = self.parse_function()
                functions.append(fn)
            except ParseError as e:
                self.errors.append(e)
                self.synchronize(TokenKind.FN, TokenKind.EOF)
                continue
            except StopIteration:
                break

        if self.errors:
            for error in self.errors:
                print(error)

        return Program(1, name, functions)

    def parse_function(self) -> FnDecl:
        # Assume function declaration looks like: fn name(param: type, ...): type { ... }
        self.expect(TokenKind.FN, "Expected 'fn' at start of function declaration")
        name_token = self.expect(TokenKind.IDENT, "Expected function name")
        self.expect(TokenKind.LPAREN, "Expected '(' after function name")
        params: List[Param] = []
        if self.current.kind != TokenKind.RPAREN:
            while True:
                param_name = self.expect(TokenKind.IDENT, "Expected parameter name")
                self.expect(TokenKind.COLON, "Expected ':' after parameter name")
                param_type = self.expect(TokenKind.IDENT, "Expected parameter type")
                params.append(Param(param_name.line, param_name.lexeme, param_type.lexeme))
                if not self.match_consume(TokenKind.COMMA):
                    break
        self.expect(TokenKind.RPAREN, "Expected ')' after parameters")
        self.expect(TokenKind.COLON, "Expected ':' before return type")
        return_type_token = self.expect(TokenKind.IDENT, "Expected return type")
        body = self.parse_block()
        return FnDecl(
            name_token.line, name_token.lexeme, params, return_type_token.lexeme, body
        )

    def parse_block(self) -> Body:
        self.expect(TokenKind.LBRACE, "Expected '{' to start block")
        statements = []
        while not self.match(TokenKind.RBRACE, TokenKind.EOF):
            try:
                stmt = self.parse_stmt()
                statements.append(stmt)
            except ParseError as e:
                # if there is an error sync to the next statement or block end
                self.errors.append(e)
                self.synchronize(
                    TokenKind.LET,
                    TokenKind.CONST,
                    TokenKind.IF,
                    TokenKind.GOTO,
                    TokenKind.LABEL,
                    TokenKind.RETURN,
                    TokenKind.RBRACE,
                    TokenKind.EOF,
                )
                continue
        self.expect(TokenKind.RBRACE, "Expected '}' to end block")
        return Body(self.previous.line, statements)

    def parse_stmt(self) -> Stmt:
        if self.match_consume(TokenKind.LET):
            return self.parse_var_decl(True)
        elif self.match_consume(TokenKind.CONST):
            return self.parse_var_decl(False)
        elif self.match_consume(TokenKind.IF):
            return self.parse_if()
        elif self.match_consume(TokenKind.GOTO):
            return self.parse_goto()
        elif self.match_consume(TokenKind.RETURN):
            return self.parse_return()
        elif self.match_consume(TokenKind.LABEL):
            return self.parse_label()
        else:
            return self.parse_expr_stmt()

    def parse_var_decl(self, mutable: bool) -> VarDecl:
        start_line = self.previous.line
        name = self.expect(TokenKind.IDENT, "Expected variable name")
        self.expect(TokenKind.COLON, "Expected ':' after variable name")
        type = self.expect(TokenKind.IDENT, "Expected variable type")
        self.expect(TokenKind.EQ, "Expected '=' after variable type")
        value = self.parse_expr()
        self.expect(TokenKind.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(start_line, mutable, type.lexeme, name.lexeme, value)

    def parse_if(self) -> If:
        # advance over if
        start_line = self.previous.line
        condition = self.parse_expr()
        body = self.parse_block()
        if self.match_consume(TokenKind.ELSE):
            if self.match_consume(TokenKind.IF):
                else_branch = self.parse_if()
            else:
                else_branch = self.parse_block()
        else:
            else_branch = None
        return If(start_line, condition, body, else_branch)

    def parse_goto(self) -> Goto:
        start_line = self.previous.line
        label = self.expect(TokenKind.IDENT, "Expected label name")
        self.expect(TokenKind.SEMICOLON, "Expected ';' after goto")
        return Goto(start_line, label.lexeme)

    def parse_label(self) -> Label:
        start_line = self.previous.line
        label = self.expect(TokenKind.IDENT, "Expected label name")
        self.expect(TokenKind.COLON, "Expected ':' after label name")
        return Label(start_line, label.lexeme)

    def parse_return(self) -> Return:
        start_line = self.previous.line
        if self.match_consume(TokenKind.SEMICOLON):
            return Return(start_line, None)
        value = self.parse_expr()
        self.expect(TokenKind.SEMICOLON, "Expected ';' after return")
        return Return(start_line, value)

    def parse_expr_stmt(self) -> ExprStmt:
        expr = self.parse_expr()
        self.expect(TokenKind.SEMICOLON, "Expected ';' after expression")
        return ExprStmt(expr.line, expr)

    def get_precedence(self) -> int:
        return self.precedences.get(self.current.kind, 0)

    def parse_number(self, token: Token) -> Expr:
        try:
            if '.' in token.lexeme:
                return FloatLit(token.line, float(token.lexeme))
            return IntLit(token.line, int(token.lexeme))
        except ValueError:
            raise ParseError(f"Invalid numeric literal: {token.lexeme}", token.line, token.lexeme)

    def parse_identifier(self, token: Token) -> Expr:
        return Ident(token.line, token.lexeme)
    
    def parse_bool(self, token: Token) -> Expr:
        return BoolLit(token.line, token.lexeme == "true")

    def parse_grouping(self) -> Expr:
        expr = self.parse_expr()
        self.expect(TokenKind.RPAREN, "Expected ')' after expression")
        return expr

    def parse_infix_binary(self, left: Expr, token: Token) -> Expr:
        if token.kind == TokenKind.EQ:
            # Right-associative for assignment
            right = self.parse_expr(self.precedences[token.kind] - 1)
            return Assign(left.line, left, right)
        
        precedence = self.precedences[token.kind]
        right = self.parse_expr(precedence)
        return Binary(token.line, left, token.lexeme, right)
    
    def parse_call(self, callee: Expr, token: Token) -> Expr:
        args: List[Expr] = []
        if not self.match(TokenKind.RPAREN):
            while True:
                args.append(self.parse_expr(0))
                if not self.match_consume(TokenKind.COMMA):
                    break
        self.expect(TokenKind.RPAREN, "Expected ')' after function arguments")
        return Call(token.line, callee, args)
    
    def parse_unary(self, token: Token) -> Expr:
        operand = self.parse_expr(9)
        return Unary(token.line, token.lexeme, operand)

    def parse_expr(self, precedence=0) -> Expr:
        token = self.current
        self.advance()

        prefix = self.prefix_parse_fns.get(token.kind)
        if not prefix:
            raise ParseError(
                f"No prefix parse function for {token.kind}", token.line, token.lexeme
            )

        left = prefix(token)

        while precedence < self.get_precedence():
            token = self.current
            self.advance()

            infix = self.infix_parse_fns.get(token.kind)
            if not infix:
                break

            left = infix(left, token)

        return left
