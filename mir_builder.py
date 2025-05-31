from mir import Block, Function, Goto, Module, Return
from toycast import Assign, Body, ExprStmt, FnDecl, If, Label, Program, Stmt, VarDecl


class MirBuilder:
    def __init__(self) -> None:
        self.module: Module = Module("placeholder")
        self.current_function: Function = Function("placeholder", {}, {}, "void")
        self.current_block: Block = Block("placeholder", [])

    def lower(self, program: Program) -> Module:
        self.module = Module(program.name)

        for function in program.functions:
            self.lower_function(function)

        return self.module
    
    def enter_block(self, name: str) -> Block:
        # search for the block in the current function
        block = self.current_function.blocks.get(name)
        if block is not None:
            self.current_block = block
            return block
        # if it doesn't exist, create it
        block = Block(name, [])
        self.current_function.blocks[name] = block
        self.current_block = block
        return block
        
    
    def lower_function(self, function: FnDecl) -> None:
        # create a new function
        self.current_function = Function(function.name, {}, {}, function.return_type)
        # add the function params to the function
        for param in function.params:
            # this is easy because the types are just string for now
            self.current_function.new_param(param.name, param.type)
        # create an entry block
        self.enter_block("_entry")
        # lower the function body
        self.lower_body(function.body)
        
        
    def lower_body(self, body: Body) -> None:
        for stmt in body:
            self.lower_stmt(stmt)
            
    def lower_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            self.lower_var_decl(stmt)
        elif isinstance(stmt, Assign):
            self.lower_assign(stmt)
        elif isinstance(stmt, If):
            self.lower_if(stmt)
        elif isinstance(stmt, Goto):
            self.lower_goto(stmt)
        elif isinstance(stmt, Label):
            self.lower_label(stmt)
        elif isinstance(stmt, Return):
            self.lower_return(stmt)
        elif isinstance(stmt, ExprStmt):
            self.lower_expr_stmt(stmt)
            
            
    def lower_var_decl(self, stmt: VarDecl) -> None:
        # TODO: implement
        pass
    
    def lower_assign(self, stmt: Assign) -> None:
        # TODO: implement
        pass
    
    def lower_if(self, stmt: If) -> None:
        # TODO: implement
        pass
    
    def lower_goto(self, stmt: Goto) -> None:
        # TODO: implement
        pass
    
    def lower_label(self, stmt: Label) -> None:
        # TODO: implement
        pass
    
    def lower_return(self, stmt: Return) -> None:
        # TODO: implement
        pass
    
    def lower_expr_stmt(self, stmt: ExprStmt) -> None:
        # TODO: implement
        pass