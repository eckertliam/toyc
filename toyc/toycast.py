# the ast for toyc
from dataclasses import dataclass
from abc import ABC
from typing import Iterator, List, Optional, Union


@dataclass(slots=True, frozen=True)
class AstNode(ABC):
    line: int


@dataclass(slots=True, frozen=True)
class Stmt(AstNode):
    pass


@dataclass(slots=True, frozen=True)
class Expr(AstNode):
    pass


@dataclass(slots=True, frozen=True)
class Body(AstNode):
    statements: List[Stmt]

    def __iter__(self) -> Iterator[Stmt]:
        return iter(self.statements)


@dataclass(slots=True, frozen=True)
class Param(AstNode):
    name: str
    type: str


@dataclass(slots=True, frozen=True)
class FnDecl(AstNode):
    name: str
    params: List[Param]
    return_type: str
    body: Body


@dataclass(slots=True)
class Program:
    name: str
    functions: List[FnDecl]


@dataclass(slots=True, frozen=True)
class VarDecl(Stmt):
    mutable: bool
    type: str
    name: str
    value: Expr


@dataclass(slots=True, frozen=True)
class Assign(Stmt, Expr):
    left: Expr
    right: Expr


@dataclass(slots=True, frozen=True)
class If(Stmt):
    condition: Expr
    then_branch: Body
    else_branch: Optional[Union[Body, "If"]]


@dataclass(slots=True, frozen=True  )
class Goto(Stmt):
    label: str


@dataclass(slots=True, frozen=True)
class Label(Stmt):
    label: str


@dataclass(slots=True, frozen=True)
class Return(Stmt):
    value: Optional[Expr]


@dataclass(slots=True, frozen=True)
class ExprStmt(Stmt):
    expr: Expr


@dataclass(slots=True, frozen=True)
class Call(Expr):
    callee: Expr
    args: List[Expr]


@dataclass(slots=True, frozen=True)
class IntLit(Expr):
    value: int


@dataclass(slots=True, frozen=True)
class FloatLit(Expr):
    value: float


@dataclass(slots=True, frozen=True)
class BoolLit(Expr):
    value: bool


@dataclass(slots=True, frozen=True)
class Ident(Expr):
    name: str


@dataclass(slots=True, frozen=True)
class Unary(Expr):
    op: str
    operand: Expr


@dataclass(slots=True, frozen=True)
class Binary(Expr):
    left: Expr
    op: str
    right: Expr
