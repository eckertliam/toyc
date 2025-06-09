import argparse
import sys
import os
from toyc.scanner import Scanner
from toyc.parser import Parser
from toyc.codegen import LLVMCodeGen
import llvmlite.binding as llvm
import subprocess


def compile_source(src: str, prog_name: str):
    # compile the source to LLVM IR
    # Lex and parse
    scanner = Scanner(src)
    tokens = iter(scanner)
    parser = Parser(tokens)
    ast = parser.parse_program(prog_name)
    # Lower to LLVM IR
    llvm_mod = LLVMCodeGen().lower(ast)
    return llvm_mod


# AOT compilation: emit object and link to native executable
def aot_compile(llvm_ir: str, obj_path: str, exe_path: str):
    # Initialize LLVM backends
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # Parse and verify IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()

    # Create and configure TargetMachine
    target = llvm.Target.from_default_triple()
    tm = target.create_target_machine()

    # Emit object file
    obj_bytes = tm.emit_object(mod)
    with open(obj_path, "wb") as f:
        f.write(obj_bytes)

    # Link into executable (uses system clang)
    subprocess.run(["clang", obj_path, "-o", exe_path], check=True)


def main():
    argp = argparse.ArgumentParser(
        description="ToyC compiler: .toyc -> native executable (AOT) or JIT execution"
    )
    argp.add_argument("input", help="Input .toyc source file")
    argp.add_argument(
        "-o", "--output", help="Output executable path, default <input basename>"
    )
    argp.add_argument(
        "--jit", action="store_true", help="JIT-execute the generated IR instead of AOT"
    )
    args = argp.parse_args()

    # Read input file
    try:
        with open(args.input, "r") as f:
            src = f.read()
    except IOError as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    prog_name = os.path.splitext(os.path.basename(args.input))[0]

    try:
        llvm_mod = compile_source(src, prog_name)
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        sys.exit(1)

    # convert to LLVM IR text
    ir_text = str(llvm_mod)
    if args.jit:
        # jit execution path
        # initialize LLVM backends
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        # parse and verify IR
        mod = llvm.parse_assembly(ir_text)
        mod.verify()
        # create target machine and engine
        target = llvm.Target.from_default_triple()
        tm = target.create_target_machine()
        # create MCJIT compiler
        engine = llvm.create_mcjit_compiler(mod, tm)
        # finalize object
        engine.finalize_object()
        # get pointer to 'main' function
        ptr = engine.get_function_address(prog_name)
        # create ctypes function pointer
        from ctypes import CFUNCTYPE, c_int

        cfunc = CFUNCTYPE(c_int)(ptr)
        # call function and print result
        result = cfunc()
        print(f"JIT returned: {result}")
    else:
        # aot compile: emit object and link to native executable
        exe_path = args.output if args.output else prog_name
        obj_path = exe_path + ".o"
        try:
            aot_compile(ir_text, obj_path, exe_path)
        except Exception as e:
            print(f"Linking error: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Generated executable: {exe_path}")


if __name__ == "__main__":
    main()
