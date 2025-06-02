from llvmlite import ir
from typing import Dict
import toycast as tc


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

    def lower(self, program: tc.Program) -> ir.Module:
        # lower every function in the MIR module
        for fn in program.functions:
            self.lower_function(fn)
        return self.module

    def lower_function(self, fn: tc.FnDecl) -> None:
        # create LLVM function signature
        ret_ty = self.type_map(fn.return_type)
        param_tys = [self.type_map(param.type) for param in fn.params]
        fn_ty = ir.FunctionType(ret_ty, param_tys)
        self.func = ir.Function(self.module, fn_ty, name=fn.name)

        # name the incoming parameters
        for llvm_arg, param in zip(self.func.args, fn.params):
            llvm_arg.name = param.name

        # create an entry basic block and attach the builder
        entry_block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)

        # allocate space for parameters
        for llvm_arg in self.func.args:
            alloca = self.builder.alloca(llvm_arg.type, name=llvm_arg.name)
            self.builder.store(llvm_arg, alloca)
            self.reg_map[llvm_arg.name] = alloca

        # lower the body
        self.lower_body(fn.body)

    def lower_body(self, body: tc.Body) -> None:
        for stmt in body.statements:
            self.lower_stmt(stmt)

    def lower_stmt(self, stmt: tc.Stmt) -> None:
        if isinstance(stmt, tc.VarDecl):
            self.lower_var_decl(stmt)
        elif isinstance(stmt, tc.Assign):
            self.lower_assign(stmt)
        elif isinstance(stmt, tc.Return):
            self.lower_return(stmt)
        elif isinstance(stmt, tc.ExprStmt):
            self.lower_expr(stmt.expr)
        elif isinstance(stmt, tc.If):
            self.lower_if(stmt)
        elif isinstance(stmt, tc.Label):
            self.lower_label(stmt)
        elif isinstance(stmt, tc.Goto):
            self.lower_goto(stmt)
        else:
            raise NotImplementedError(f"Unknown Stmt: {stmt}")

    def lower_var_decl(self, decl: tc.VarDecl) -> None:
        alloca = self.builder.alloca(self.type_map(decl.type), name=decl.name)
        value = self.lower_expr(decl.value)
        self.builder.store(value, alloca)
        self.reg_map[decl.name] = alloca

    def lower_assign(self, assign: tc.Assign) -> None:
        if isinstance(assign.left, tc.Ident):
            ptr = self.reg_map[assign.left.name]
            value = self.lower_expr(assign.right)
            self.builder.store(value, ptr)
        else:
            raise NotImplementedError("Complex l-values not implemented")

    def lower_return(self, ret: tc.Return) -> None:
        if ret.value is not None:
            retval = self.lower_expr(ret.value)
            self.builder.ret(retval)
        else:
            self.builder.ret_void()

    def lower_expr(self, expr: tc.Expr) -> ir.Value:
        if isinstance(expr, tc.IntLit):
            return ir.Constant(ir.IntType(32), expr.value)
        elif isinstance(expr, tc.FloatLit):
            return ir.Constant(ir.FloatType(), expr.value)
        elif isinstance(expr, tc.BoolLit):
            return ir.Constant(ir.IntType(1), int(expr.value))
        elif isinstance(expr, tc.Ident):
            ptr = self.reg_map[expr.name]
            return self.builder.load(ptr)
        elif isinstance(expr, tc.Assign):
            # handle assignment expression: store RHS into LHS and return the RHS value
            assert isinstance(expr.left, tc.Ident), "Only simple Ident LHS assignments supported"
            ptr = self.reg_map[expr.left.name]
            val = self.lower_expr(expr.right)
            self.builder.store(val, ptr)
            return val
        elif isinstance(expr, tc.Binary):
            left = self.lower_expr(expr.left)
            right = self.lower_expr(expr.right)
            return self.lower_binary(expr.op, left, right)
        elif isinstance(expr, tc.Unary):
            return self.lower_unary(expr)
        elif isinstance(expr, tc.Call):
            # TODO: remove once we support more complex callees
            assert isinstance(
                expr.callee, tc.Ident
            ), f"Expected Ident, got {type(expr.callee)}"
            callee = self.module.globals.get(expr.callee.name)
            args = [self.lower_expr(arg) for arg in expr.args]
            return self.builder.call(callee, args)
        else:
            raise NotImplementedError(f"Unknown Expr: {expr}")

    def lower_binary(self, op: str, left: ir.Value, right: ir.Value) -> ir.Value:
        if op == "+":
            return self.builder.add(left, right)  # type: ignore
        elif op == "-":
            return self.builder.sub(left, right)  # type: ignore
        elif op == "*":
            return self.builder.mul(left, right)  # type: ignore
        elif op == "/":
            return self.builder.sdiv(left, right)  # type: ignore
        elif op == "==":
            return self.builder.icmp_signed("==", left, right)
        elif op == ">":
            return self.builder.icmp_signed(">", left, right)
        elif op == "<":
            return self.builder.icmp_signed("<", left, right)
        elif op == ">=":
            return self.builder.icmp_signed(">=", left, right)
        elif op == "<=":
            return self.builder.icmp_signed("<=", left, right)
        elif op == "!=":
            return self.builder.icmp_signed("!=", left, right)
        else:
            raise NotImplementedError(f"Unknown binary operator: {op}")

    def lower_unary(self, unary: tc.Unary) -> ir.Value:
        """
        Lower a unary operation. Supports integer negation, floating-point negation, and boolean negation.
        """
        operand_val = self.lower_expr(unary.operand)
        # integer negation: -x
        if unary.op == "-":
            # if operand is float or double, use fneg; for integers, use neg
            if isinstance(operand_val.type, ir.IntType): # type: ignore
                return self.builder.neg(operand_val)  # type: ignore
            else:
                return self.builder.fneg(operand_val)  # type: ignore
        # boolean negation: !x (i.e., x == 0 yields true)
        elif unary.op == "!":
            zero = ir.Constant(operand_val.type, 0) # type: ignore
            return self.builder.icmp_signed("==", operand_val, zero)
        else:
            raise NotImplementedError(f"Unknown unary operator: {unary.op}")

    def lower_if(self, stmt: tc.If) -> None:
        # evaluate the condition expression (should yield an i1 boolean)
        cond_val = self.lower_expr(stmt.condition)

        # create the “then” block; we’ll decide about a continuation later
        then_block = self.func.append_basic_block(name=f"then_{stmt.line}")

        if stmt.else_branch:
            # create the “else” block
            else_block = self.func.append_basic_block(name=f"else_{stmt.line}")

            # conditional branch: if cond then then_block else else_block
            self.builder.cbranch(cond_val, then_block, else_block)

            # emit 'then' block
            self.builder.position_at_start(then_block)
            self.lower_body(stmt.then_branch)
            assert self.builder.block is not None, "Builder block is None"
            then_terminated = self.builder.block.is_terminated

            # emit 'else' block
            self.builder.position_at_start(else_block)
            if isinstance(stmt.else_branch, tc.Body):
                self.lower_body(stmt.else_branch)
            else:
                # handle 'else if' chain
                self.lower_if(stmt.else_branch)
            assert self.builder.block is not None, "Builder block is None"
            else_terminated = self.builder.block.is_terminated

            # only create a continuation block if either branch didn't terminate
            if not then_terminated or not else_terminated:
                cont_block = self.func.append_basic_block(name=f"ifcont_{stmt.line}")
                # if “then” didn’t terminate, branch to continuation
                if not then_terminated:
                    # move builder to end of then_block to emit branch
                    # (builder is already at end of else_block; we need to insert prior)
                    # instead, you can insert branch before moving the builder after lowering then_branch
                    pass  # already handled by checking is_terminated above before leaving then_block
                # if “else” didn’t terminate, branch to continuation
                if not else_terminated:
                    pass  # already handled by checking is_terminated above before leaving else_block

                # position builder at continuation
                self.builder.position_at_start(cont_block)
            else:
                # both branches ended in a terminator → no continuation needed
                return
        else:
            # no else branch → always need a continuation block, because false-path falls through
            cont_block = self.func.append_basic_block(name=f"ifcont_{stmt.line}")
            self.builder.cbranch(cond_val, then_block, cont_block)

            # emit 'then' block
            self.builder.position_at_start(then_block)
            self.lower_body(stmt.then_branch)
            assert self.builder.block is not None, "Builder block is None"
            if not self.builder.block.is_terminated:
                self.builder.branch(cont_block)

            # position at continuation
            self.builder.position_at_start(cont_block)

    def lower_label(self, stmt: tc.Label) -> None:
        label_name = stmt.label
        # create the block if it doesn't exist
        if label_name not in self.block_map:
            new_block = self.func.append_basic_block(name=label_name)
            self.block_map[label_name] = new_block
        else:
            new_block = self.block_map[label_name]

        # if the current block has no terminator, explicitly branch to the label block
        if self.builder.block is not None and not self.builder.block.is_terminated:
            self.builder.branch(new_block)

        # position builder at the start of the label block
        self.builder.position_at_start(new_block)

    def lower_goto(self, stmt: tc.Goto) -> None:
        label_name = stmt.label
        # create the block if it doesn't exist yet
        if label_name not in self.block_map:
            target_block = self.func.append_basic_block(name=label_name)
            self.block_map[label_name] = target_block
        else:
            target_block = self.block_map[label_name]

        # emit an unconditional branch to the target block
        self.builder.branch(target_block)
        # after a branch, subsequent instructions should be placed in a new, unnamed block
        # to avoid inserting into a terminated block; create a placeholder continuation block
        continuation = self.func.append_basic_block(name=f"after_goto_{stmt.line}")
        self.builder.position_at_start(continuation)
