from llvmlite import ir
from typing import Dict
from mir import (
    Module as MirModule,
    Function as MirFunction,
    Register,
    Block,
    Instruction,
    Call as MirCall,
    Return as MirReturn,
    Branch as MirBranch,
    Goto as MirGoto,
    Store as MirStore,
    Load as MirLoad,
    BinaryOp,
    BinOpKind,
    UnaryOp,
    UnaryOpKind,
)


class LLVMCodeGen:
    module: ir.Module
    builder: ir.IRBuilder
    func: ir.Function
    reg_map: Dict[str, ir.AllocaInstr]
    block_map: Dict[str, ir.Block]

    def __init__(self):
        # the top-level LLVM IR module
        self.module = ir.Module(name="toyc_module")
        # initialize register and block maps
        self.reg_map = {}
        self.block_map = {}

    def type_map(self, ty: str) -> ir.Type:
        # map our MIR type strings to llvmlite IR types
        if ty == "i32":
            return ir.IntType(32)
        elif ty == "i64":
            return ir.IntType(64)
        elif ty == "f32":
            return ir.FloatType()
        elif ty == "f64":
            return ir.DoubleType()
        elif ty == "bool":
            return ir.IntType(1)
        elif ty == "void":
            return ir.VoidType()
        else:
            raise NotImplementedError(f"Unknown MIR type: {ty}")

    def lower(self, mir_mod: MirModule) -> ir.Module:
        # lower every function in the MIR module
        for fn in mir_mod.functions.values():
            self.lower_function(fn)
        return self.module

    def lower_function(self, fn: MirFunction) -> None:
        # create LLVM function signature
        ret_ty = self.type_map(fn.return_type)
        param_tys = [self.type_map(reg.type) for reg in fn.params.values()]
        fn_ty = ir.FunctionType(ret_ty, param_tys)
        self.func = ir.Function(self.module, fn_ty, name=fn.name)
        # name the incoming parameters
        for llvm_arg, (name, _) in zip(self.func.args, fn.params.items()):
            llvm_arg.name = name

        # create LLVM basic blocks for each MIR block
        for block_name in fn.blocks:
            self.block_map[block_name] = self.func.append_basic_block(name=block_name)

        # position builder in the entry block and allocate all MIR registers
        entry_name = next(iter(fn.blocks))
        entry_bb = self.block_map[entry_name]
        self.builder = ir.IRBuilder(entry_bb)
        for name, reg in fn.registers.items():
            ptr = self.builder.alloca(self.type_map(reg.type), name=name)
            self.reg_map[name] = ptr

        # store the initial function arguments into the corresponding allocas
        for llvm_arg in self.func.args:
            self.builder.store(llvm_arg, self.reg_map[llvm_arg.name])

        # lower each block and its instructions
        for block_name, block in fn.blocks.items():
            bb = self.block_map[block_name]
            self.builder.position_at_end(bb)
            for instr in block.instructions:
                self.lower_instr(instr)

        # ensure last block has a terminator: ret void or default zero return
        if not bb.is_terminated:
            if isinstance(ret_ty, ir.VoidType):
                self.builder.ret_void()
            else:
                # default return zero for non-void
                zero = ir.Constant(ret_ty, 0)
                self.builder.ret(zero)

    def get_value(self, val):
        # retrieve an LLVM IR Value for a MIR Value
        if isinstance(val, Register):
            ptr = self.reg_map[val.name]
            return self.builder.load(ptr, name=val.name + "_val")
        elif isinstance(val, bool):
            return ir.Constant(ir.IntType(1), int(val))
        elif isinstance(val, int):
            return ir.Constant(ir.IntType(32), val)
        elif isinstance(val, float):
            return ir.Constant(ir.FloatType(), val)
        else:
            raise NotImplementedError(f"Unsupported MIR value type: {type(val)}")

    def lower_instr(self, instr: Instruction) -> None:
        # dispatch on MIR instruction kind
        if isinstance(instr, MirReturn):
            if instr.value is None:
                self.builder.ret_void()
            else:
                self.builder.ret(self.get_value(instr.value))
        elif isinstance(instr, MirGoto):
            self.builder.branch(self.block_map[instr.target])
        elif isinstance(instr, MirBranch):
            cond = self.get_value(instr.condition)
            self.builder.cbranch(cond,
                                 self.block_map[instr.then_br],
                                 self.block_map[instr.else_br])
        elif isinstance(instr, MirStore):
            val = self.get_value(instr.value)
            self.builder.store(val, self.reg_map[instr.reg.name])
        elif isinstance(instr, MirLoad):
            loaded = self.builder.load(self.reg_map[instr.reg.name],
                                       name=instr.result.name)
            self.builder.store(loaded, self.reg_map[instr.result.name])
        elif isinstance(instr, BinaryOp):
            l = self.get_value(instr.left)
            r = self.get_value(instr.right)
            # integer arithmetic
            if instr.op == BinOpKind.IADD:
                res = self.builder.add(l, r, name=instr.result.name)
            elif instr.op == BinOpKind.ISUB:
                res = self.builder.sub(l, r, name=instr.result.name)
            elif instr.op == BinOpKind.IMUL:
                res = self.builder.mul(l, r, name=instr.result.name)
            elif instr.op == BinOpKind.IDIV:
                res = self.builder.sdiv(l, r, name=instr.result.name)
            elif instr.op == BinOpKind.IREM:
                res = self.builder.srem(l, r, name=instr.result.name)
            # integer comparisons
            elif instr.op in (BinOpKind.IEQ, BinOpKind.INE,
                               BinOpKind.ILT, BinOpKind.ILE,
                               BinOpKind.IGT, BinOpKind.IGE):
                pred_map = {
                    BinOpKind.IEQ: '==', BinOpKind.INE: '!=',
                    BinOpKind.ILT: '<',  BinOpKind.ILE: '<=',
                    BinOpKind.IGT: '>',  BinOpKind.IGE: '>='
                }
                res = self.builder.icmp_signed(pred_map[instr.op], l, r,
                                               name=instr.result.name)
            # boolean ops
            elif instr.op == BinOpKind.AND:
                res = self.builder.and_(l, r, name=instr.result.name)
            elif instr.op == BinOpKind.OR:
                res = self.builder.or_(l, r, name=instr.result.name)
            # float arithmetic/comparison TODO
            else:
                raise NotImplementedError(f"Unsupported BinOpKind: {instr.op}")
            self.builder.store(res, self.reg_map[instr.result.name])
        elif isinstance(instr, UnaryOp):
            v = self.get_value(instr.value)
            if instr.op == UnaryOpKind.NEG:
                res = self.builder.neg(v, name=instr.result.name)
            elif instr.op == UnaryOpKind.NOT:
                one = ir.Constant(v.type, 1)
                res = self.builder.xor(v, one, name=instr.result.name)
            else:
                raise NotImplementedError(f"Unsupported UnaryOpKind: {instr.op}")
            self.builder.store(res, self.reg_map[instr.result.name])
        elif isinstance(instr, MirCall):
            # assume calls return an i32 by default
            callee = self.module.get_global(instr.callee)
            args = [self.get_value(a) for a in instr.args]
            call_res = self.builder.call(callee, args,
                                         name=instr.callee + "_res")
            # optional: store result if target register exists
            if isinstance(instr, BinaryOp): pass  # no-op
        else:
            raise NotImplementedError(f"Unsupported instruction: {instr}")
