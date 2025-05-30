from enum import Enum, auto
from dataclasses import dataclass


class TokenKind(Enum):
    # Literals
    NUMBER = auto()
    IDENT = auto()
    TRUE = auto()
    FALSE = auto()

    # Keywords
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

    # End of file
    EOF = auto()
    ERROR = auto()


@dataclass(slots=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
