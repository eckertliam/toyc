# ToyC

A toy language compiler written in Python. For educational purposes.


# ToyC

ToyC is a simple, educational compiler for a C‑inspired toy language, implemented in Python. It demonstrates the end‑to‑end process of parsing source code, building an abstract syntax tree (AST), generating intermediate representation (IR) using LLVM via llvmlite, and emitting executable binaries. ToyC is designed to help learners understand compiler construction fundamentals in a hands-on way.

## Features

- **Parser and AST**: ToyC includes a hand‑written parser that converts source code into an AST.
- **LLVM IR Generation**: Uses llvmlite to lower the AST into LLVM IR, including support for variables, arithmetic, conditionals (`if`/`else`), labels/gotos, and functions.
- **Code Emission**: Generates object files or executables by invoking LLVM’s code generation pipeline.
- **Educational Focus**: Clear, well‑documented code, with each compiler stage visible to the learner.

## Getting Started

### Prerequisites

- Python 3.8 or newer
- [llvmlite](https://llvmlite.readthedocs.io/en/latest/installation.html) (for IR-level code generation)
- [LLVM](https://llvm.org/) toolchain installed (e.g., `clang`, `llc`, `llvm-as`, `llvm-ld`) if emitting final binaries
- [poetry](https://python-poetry.org/) for Python package management

### Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/YourUsername/toyc.git
   cd toyc
   ```

2. **Create a virtual environment (recommended)**  
   ```bash
   poetry shell
   ```

3. **Install Python dependencies**  
   ```bash
   poetry install
   ```  

## Language Overview

ToyC’s syntax is loosely based on a subset of C. The current implementation supports:

### Basic Syntax

- **Variable Declarations**  
  ```c
  let x: i32 = 10;
  let flag: bool = true;
  ```

- **Arithmetic and Boolean Operations**  
  ```c
  let sum: i32 = a + b;
  let result: bool = (x < 5) && (y >= 2);
  ```

- **Return Statements**  
  ```c
  return x;
  ```

### Control Flow

- **If/Else**  
  ```c
  if x < 10 {
      x = x + 1;
  } else {
      x = x - 1;
  }
  ```

- **Labels & Goto**  
  ```c
  label loop:
      if x < 5 {
          x = x + 1;
          goto loop;
      }
  ```

### Functions

- **Function Definition**  
  ```c
  fn add(a: i32, b: i32): i32 {
      return a + b;
  }
  ```

- **`main` Function Entry Point**  
  The compiler expects a `fn main(): i32 { ... }` entry point. The returned integer will be used as the program’s exit code.

## Building a Program

ToyC’s main driver script is `main.py`. To compile a `.tc` source file:

```bash
poetry run python main.py path/to/source.tc
```

or to JIT:

```bash
poetry run python main.py path/to/source.tc --jit
```


This will:

1. Parse `source.tc` into an AST.
2. Perform semantic checks (type validation, undefined identifiers, etc.).
3. Lower the AST into LLVM IR using llvmlite.
4. Either JIT or AOT compile the IR to an executable.

For example to see quit JIT reuslts:

```bash
poetry run python main.py examples/loop.tc --jit
```

## Examples

Here are some examples of ToyC programs:

```c
fn main(): i32 {
    let a: i32 = 1;
    return a;
}
```
Compiles, prints nothing, and returns exit code `1`.


```c
fn factorial(n: i32): i32 {
    if n <= 1 {
        return 1;
    }
    let sub: i32 = n - 1;
    let rec: i32 = factorial(sub);
    return n * rec;
}

fn main(): i32 {
    let result: i32 = factorial(5);
    return result;
}
```
Computes `5! = 120` and returns `120` as exit code.

```c
fn main(): i32 {
    let i: i32 = 0;
    label loop:
        if i < 3 {
            i = i + 1;
            goto loop;
          }
    return i;
}
```
Demonstrates labels, conditional branches, and gotos.

## Project Structure

```
ToyC/
├── codegen.py        # IR lowering and LLVM builder logic
├── parser.py         # Lexing and parsing into AST
├── ast.py            # AST node definitions
├── main.py           # Compiler driver (parsing → IR → emit)
├── examples/         # Sample .tc source files
└── README.md         # This file
```

- **`ast.py`**: Defines classes for expressions, statements, function declarations, etc.
- **`parser.py`**: Converts `*.tc` text into an instance of the AST.
- **`codegen.py`**: Lowers AST nodes into LLVM IR using llvmlite’s `ir` builder.
- **`main.py`**: Entry point that ties all stages together and writes out the final IR.

## License

This project is released under the Apache License 2.0. See [LICENSE](LICENSE) for details.
