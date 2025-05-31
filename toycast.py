# the ast for toyc
from dataclasses import dataclass
from abc import ABC
from typing import Dict, Iterator, List, Optional, Union

@dataclass(slots=True)
class AstNode(ABC):
    line: int

@dataclass(slots=True)
class Stmt(AstNode):
    pass

@dataclass(slots=True)
class Expr(AstNode):
    pass

@dataclass(slots=True)
class Body(AstNode):
    statements: List[Stmt]
    
    def __iter__(self) -> Iterator[Stmt]:
        return iter(self.statements)

@dataclass(slots=True)
class Param(AstNode):
    name: str
    type: str

@dataclass(slots=True)
class FnDecl(AstNode):
    name: str
    params: List[Param]
    return_type: str
    body: Body

@dataclass(slots=True)
class Program(AstNode):
    name: str
    functions: List[FnDecl]
    
@dataclass(slots=True)
class VarDecl(Stmt):
    mutable: bool
    type: str
    name: str
    value: Expr
    
@dataclass(slots=True)
class Assign(Expr, Stmt):
    left: Expr
    right: Expr
    
@dataclass(slots=True)
class If(Stmt):
    condition: Expr
    then_branch: Body
    else_branch: Optional[Union[Body, 'If']]
    
@dataclass(slots=True)
class Goto(Stmt):
    label: str
    
@dataclass(slots=True)
class Label(Stmt):
    label: str
    
@dataclass(slots=True)
class Return(Stmt):
    value: Optional[Expr]
    
@dataclass(slots=True)
class ExprStmt(Stmt):
    expr: Expr
    
@dataclass(slots=True)
class Call(Expr):
    callee: Expr
    args: List[Expr]
    
@dataclass(slots=True)
class IntLit(Expr):
    value: int
    
@dataclass(slots=True)
class FloatLit(Expr):
    value: float
    
@dataclass(slots=True)
class BoolLit(Expr):
    value: bool
    
@dataclass(slots=True)
class Ident(Expr):
    name: str
    
@dataclass(slots=True)
class Unary(Expr):
    op: str
    operand: Expr
    
@dataclass(slots=True)
class Binary(Expr):
    left: Expr
    op: str
    right: Expr
