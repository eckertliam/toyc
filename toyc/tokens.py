# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Liam Eckert

"""
ToyC Tokens
===========

Central definitions for lexical tokens used throughout the ToyC compiler.

Public API
----------
TokenKind
    Enumeration of all possible lexical token categories.
Token
    Lightweight, immutable container holding a concrete token instance
    produced by the scanner.
"""

from enum import Enum, auto
from dataclasses import dataclass


class TokenKind(Enum):
    """Enumeration of every lexical token understood by ToyC.

    The members roughly follow three conceptual groups:

    * **Literals & identifiers** – user‑authored data like numbers and names.
    * **Keywords & operators** – reserved language terms and arithmetic/logic symbols.
    * **Punctuation & control** – structural delimiters plus EOF and error sentinels.
    """

    # Literals
    NUMBER = auto()
    IDENT = auto()
    TRUE = auto()
    FALSE = auto()

    # Keywords
    LET = auto()
    CONST = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    GOTO = auto()
    LABEL = auto()
    RETURN = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    MOD = auto()
    EQ = auto()
    EQEQ = auto()
    BANG = auto()
    BANGEQ = auto()
    LT = auto()
    LTEQ = auto()
    GT = auto()
    GTEQ = auto()
    AMPAMP = auto()
    PIPEPIPE = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMICOLON = auto()
    COLON = auto()
    COMMA = auto()

    # End of file
    EOF = auto()
    ERROR = auto()


@dataclass(slots=True, frozen=True)
class Token:
    """Concrete token produced by the scanner.

    Attributes
    ----------
    kind : TokenKind
        The category of token (keyword, identifier, etc.).
    lexeme : str
        The exact substring from the source code.
    line : int
        line number where the token originates.
    """

    kind: TokenKind
    lexeme: str
    line: int
