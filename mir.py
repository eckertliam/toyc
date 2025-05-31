from dataclasses import dataclass, field
from collections import OrderedDict
from enum import Enum
from typing import Dict, List, Union


@dataclass
class Module:
    name: str
    functions: Dict[str, "Function"] = field(default_factory=dict)


@dataclass
class Function:
    name: str
    registers: Dict[str, "Register"]  # register name -> register
    params: Dict[str, "Register"]  # param name -> param register
    return_type: str  # return type
    blocks: OrderedDict[str, "Block"] = field(default_factory=OrderedDict)

    def new_register(self, name: str, type: str) -> "Register":
        if name in self.registers:
            raise ValueError(
                f"Register {name} already exists in function {self.name} as {self.registers[name].name}"
            )

        # create a new register
        register = Register(name, type)
        # add it to the registers dict
        self.registers[name] = register
        # return the register
        return register

    def new_param(self, name: str, type: str) -> "Register":
        if name in self.params:
            raise ValueError(
                f"Parameter {name} already exists in function {self.name} as {self.params[name].name}"
            )

        # create a new register
        param = Register(name, type)
        # add it to the params dict
        self.params[name] = param
        # add it to the registers dict
        self.new_register(name, type)
        # return the register
        return param


@dataclass
class Register:
    name: str
    type: str


@dataclass
class Block:
    name: str
    instructions: List["Instruction"]


@dataclass
class Instruction:
    pass


Value = Union[Register, int, float, bool]


@dataclass
class Call(Instruction):
    callee: str
    args: List[Value]


@dataclass
class Return(Instruction):
    value: Value


@dataclass
class Branch(Instruction):
    condition: Value
    then_br: str
    else_br: str


@dataclass
class Goto(Instruction):
    target: str


@dataclass
class Store(Instruction):
    # register to store into
    reg: Register
    # value to store
    value: Value


@dataclass
class Load(Instruction):
    # register to load into
    result: Register
    # register to load from
    reg: Register


class BinOpKind(Enum):
    IADD = "iadd"
    ISUB = "isub"
    IMUL = "imul"
    IDIV = "idiv"
    IREM = "irem"
    IEQ = "ieq"
    INE = "ine"
    ILT = "ilt"
    ILE = "ile"
    IGE = "ige"
    IGT = "igt"
    FADD = "fadd"
    FSUB = "fsub"
    FMUL = "fmul"
    FDIV = "fdiv"
    FEQ = "feq"
    FNE = "fne"
    FLT = "flt"
    FLE = "fle"
    FGE = "fge"
    FGT = "fgt"
    AND = "and"
    OR = "or"


@dataclass
class BinaryOp(Instruction):
    op: BinOpKind
    result: Register
    left: Value
    right: Value


class UnaryOpKind(Enum):
    NOT = "not"
    NEG = "neg"


@dataclass
class UnaryOp(Instruction):
    op: UnaryOpKind
    result: Register
    value: Value
