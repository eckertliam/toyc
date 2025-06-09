# SPDX-License-Identifier: Apache-2.0
# Copyright 2025, Liam Eckert

"""
ToyC Scanner
============

Greedy, table‑driven lexical scanner that converts ToyC source code into a
stream of Tokens.
"""

from toyc.tokens import Token, TokenKind
from typing import Dict, Iterator, Tuple


class Scanner:
    """Lexical scanner for the ToyC language.

    Parameters
    ----------
    source : str
        Full source text to scan.

    Yields
    ------
    Token
        Token objects representing ToyC lexemes, ending with
        :pyattr:`toyc.tokens.TokenKind.EOF`.
    """

    def __init__(self, source: str) -> None:
        """Initialize scanner state for the provided source string."""
        self.source = source
        self.line = 1
        self.start = 0
        self.current = 0

        # dispatch table for single-char tokens
        self.single_char_tokens: Dict[str, TokenKind] = {
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            "{": TokenKind.LBRACE,
            "}": TokenKind.RBRACE,
            ";": TokenKind.SEMICOLON,
            ":": TokenKind.COLON,
            "+": TokenKind.PLUS,
            "-": TokenKind.MINUS,
            "*": TokenKind.STAR,
            "/": TokenKind.SLASH,
            "%": TokenKind.MOD,
            ",": TokenKind.COMMA,
        }

        # table for branching tokens key -> (match, then, else)
        self.branch_tokens: Dict[str, Tuple[str, TokenKind, TokenKind]] = {
            "=": ("=", TokenKind.EQEQ, TokenKind.EQ),
            "!": ("=", TokenKind.BANGEQ, TokenKind.BANG),
            "<": ("=", TokenKind.LTEQ, TokenKind.LT),
            ">": ("=", TokenKind.GTEQ, TokenKind.GT),
        }

        # funky two-char tokens with no single-char fallback
        self.two_char_tokens: Dict[str, Tuple[str, TokenKind]] = {
            "&": ("&", TokenKind.AMPAMP),
            "|": ("|", TokenKind.PIPEPIPE),
        }

        self.keywords: Dict[str, TokenKind] = {
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
        }

    def __iter__(self) -> Iterator[Token]:
        """Iterate lazily over tokens until end‑of‑file."""
        while not self.is_at_end():
            yield self.scan_token()
        yield Token(TokenKind.EOF, "", self.line)

    def is_at_end(self) -> bool:
        """Return True when all characters have been consumed."""
        return self.current >= len(self.source)

    def peek(self) -> str:
        """Look at the current character without consuming it; returns '\\0' at EOF."""
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def advance(self) -> str:
        """Consume the next character, update line/offset counters, and return it."""
        # grab the current character
        char = self.source[self.current]
        # increment the current position
        self.current += 1
        # if the character is a newline, increment the line number
        if char == "\n":
            self.line += 1
        # return the character
        return char

    def make_token(self, kind: TokenKind) -> Token:
        """Create a `Token` of *kind* spanning the current lexeme."""
        # grab the lexeme from the source code
        lexeme = self.source[self.start : self.current]
        # return the token with the kind, lexeme, and line number
        return Token(kind, lexeme, self.line)

    def error_token(self, message: str) -> Token:
        """Return an error `Token` carrying *message*."""
        return Token(TokenKind.ERROR, message, self.line)

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.peek() in " \t\n\r":
            self.advance()

    def scan_token(self) -> Token:
        """Scan and return the next `Token` from the source."""
        self.skip_whitespace()
        self.start = self.current
        c = self.advance()

        # check if c is a single-char token
        if c in self.single_char_tokens:
            # just return the kind with make token
            return self.make_token(self.single_char_tokens[c])

        # check if c is a branching token
        if c in self.branch_tokens:
            # unpack the match_char, then, else
            match_char, then_kind, else_kind = self.branch_tokens[c]
            # check if the next character matches the match
            if self.peek() == match_char:
                # if so skip over it and return the then kind
                self.advance()
                return self.make_token(then_kind)
            else:
                return self.make_token(else_kind)

        # check if c is a two-char token
        if c in self.two_char_tokens:
            # check if the next character is what we expect
            expected, kind = self.two_char_tokens[c]
            if self.peek() == expected:
                self.advance()
                return self.make_token(kind)
            else:
                return self.error_token(f"Expected {expected} after {c}")

        # check if c is a number
        if c.isdigit():
            return self.number()

        # check if c is a letter
        if c.isalpha() or c == "_":
            return self.identifier()

        # its an error
        return self.error_token(f"Unexpected character: {c}")

    def identifier(self) -> Token:
        """Consume an identifier or keyword and return the corresponding `Token`."""
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()

        # get the lexeme
        lexeme = self.source[self.start : self.current]
        # check if the lexeme is a keyword if not its an ident
        kind = self.keywords.get(lexeme, TokenKind.IDENT)

        return self.make_token(kind)

    def number(self) -> Token:
        """Consume a numeric literal (int or float) and return its `Token`."""

        def consume_digits() -> None:
            while self.peek().isdigit():
                self.advance()

        consume_digits()

        if self.peek() == ".":
            self.advance()
            consume_digits()

        return self.make_token(TokenKind.NUMBER)
