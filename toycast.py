# the ast for toyc
from dataclasses import dataclass
from abc import ABC
from typing import Dict, Iterator, List, Optional

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
class Block(AstNode):
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
    body: Block

@dataclass(slots=True)
class Program(AstNode):
    functions: List[FnDecl]
    
@dataclass(slots=True)
class VarDecl(Stmt):
    mutable: bool
    type: str
    name: str
    value: Expr
    
@dataclass(slots=True)
class Assign(Stmt):
    name: str
    value: Expr
    
@dataclass(slots=True)
class If(Stmt):
    condition: Expr
    then_stmt: Stmt
    else_stmt: Optional[Stmt]
    
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
class Call(Expr):
    callee: str
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
