# 🔬 Engineering Specification: How EraLang Works (Under the Hood)

This document details the exact internal execution mechanics, parsing theory, type-system verification, bytecode virtual machine architecture, and polyglot bridges powering **EraLang 2.1**.

---

## 🏛️ End-to-End System Architecture

<div align="center">
  <img src="../assets/compiler_pipeline.svg" alt="EraLang Compiler Pipeline Architecture" width="100%" />
</div>

The EraLang execution model is broken into five distinct phases:
1. **Lexical Scanning (`eralang/lexer.py`):** Source text to precise token spans.
2. **Pratt Parsing (`eralang/parser.py`):** Recursive descent with operator precedence.
3. **Static Safety Verification (`eralang/typechecker.py`):** Exhaustiveness and type-rules checking.
4. **Bytecode Compilation (`eralang/compiler.py`):** Emits serialized OpCodes and constant pools.
5. **Execution Engines:** Either the **Stack-Based Bytecode VM**, the **Tree-Walk Evaluator**, or the **AOT C Transpiler**.

---

## 1. Phase 01: Lexical Analysis & Span Tracking

The Lexer scans UTF-8 text into a linear stream of strongly typed tokens while maintaining exact file and span locations (`SourceLocation(file, line, col)`):

* **BOM Tolerance:** Automatically detects and skips UTF-8 Byte Order Marks (`0xFEFF`).
* **Operator Precedence Scanning:** Disambiguates complex multi-character tokens:
  * `@` : First-class Tensor Matrix Multiplication operator.
  * `0..<n` : Safe half-open range slice operator.
  * `=>` : Pattern matching match arm operator.
  * `->` : Function return type annotation.
* **String Escape Decoder:** Decodes `\n`, `\t`, `\r`, `\"`, `\\`, and Unicode code points without secondary allocations.

---

## 2. Phase 02: Recursive Descent Pratt Parsing

EraLang implements a **Pratt Parser** (Top-Down Operator Precedence). Instead of complex BNF grammar conflicts, each token is bound to a binding power that governs prefix and infix associativity:

### Precedence Hierarchy Table

| Precedence Level | Token Operators | Associativity | Mathematical Role |
|---|---|:---:|---|
| `LOWEST` | Statement terminators, `,`, `{`, `}` | None | Sequence delimiters |
| `ASSIGNMENT` | `=` | Right | Variable mutation (`var` only) |
| `OR` | `\|\|`, `or` | Left | Short-circuit boolean disjunction |
| `AND` | `&&`, `and` | Left | Short-circuit boolean conjunction |
| `EQUALITY` | `==`, `!=` | Left | Strict value equality |
| `COMPARISON` | `<`, `<=`, `>`, `>=` | Left | Relational ordering |
| `RANGE` | `..`, `..<` | Left | Safe slice and iterable bounds |
| `SUM` | `+`, `-` | Left | Arithmetic addition & subtraction |
| `PRODUCT` | `*`, `/`, `%` | Left | Arithmetic multiplication & division |
| **`MATMUL`** | **`@`** | **Left** | **Native Tensor Matrix Multiplication** |
| `PREFIX` | `-`, `!`, `not` | Right | Unary inversion and negation |
| `CALL` | `()`, `[]`, `.` | Left | Function invocation & member access |

---

## 3. Phase 03: Static Safety & TypeChecker

Before any code executes, the `TypeChecker` (`eralang/typechecker.py`) analyzes the AST using a scoped `SymbolTable`:

```
   [Global Scope]
       ├── Built-ins (print, len, to_str, to_int, Tensor, Some, None, Ok, Err)
       └── Standard Library Modules (math, linalg, physics, signal, fs, json...)
             │
             └── [Function Scope: compute()]
                   ├── Parameters (mass: float, velocity: float)
                   ├── Return Marker: __fn_return__ = float
                   └── [Block Scope: if statement]
                         └── Local Bindings (let kinetic_energy)
```

### The Exhaustiveness Verification Matrix
EraLang enforces compile-time handling of all possible state variants in `MatchExpr`:

* **`Option<T>` Exhaustiveness:**
  * Must handle both `Some(v)` and `None`, OR provide a catch-all wildcard `_`.
  * If `None` is unhandled, compilation fails with diagnostic `E0301`.
* **`Result<T, E>` Exhaustiveness:**
  * Must handle both `Ok(v)` and `Err(e)`, OR provide a catch-all wildcard `_`.
  * If `Err` is omitted, compilation fails with diagnostic `E0302`.
* **Immutability Enforcement:**
  * Reassigning an immutable `let` variable raises compile error `E0101`.

---

## 4. Phase 04 & 05: The Stack-Based Bytecode VM

<div align="center">
  <img src="../assets/bytecode_vm_spec.svg" alt="EraLang Bytecode Virtual Machine Architecture" width="100%" />
</div>

When executed with `era run --vm`, the compiler lowers the validated AST into a compact bytecode chunk:

### 1. The Virtual Instruction Set (OpCodes)
* `OP_CONSTANT <idx>`: Pushes a constant from `constants[]` onto the operand stack.
* `OP_GET_LOCAL <slot>`: Pushes local variable from stack frame slot.
* `OP_SET_LOCAL <slot>`: Assigns value from top of stack to local slot.
* `OP_MATMUL`: Pops right matrix `B`, pops left matrix `A`, computes $A \times B$, and pushes result tensor.
* `OP_CALL <n_args>`: Sets up a new `CallFrame`, transfers instruction pointer (`ip`), and branches.
* `OP_RETURN`: Tears down `CallFrame`, preserves return value, and restores previous stack base.

### 2. Execution Loop
```python
while self.ip < len(chunk.instructions):
    opcode = chunk.instructions[self.ip]
    if opcode == OpCode.OP_ADD:
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.push(a + b)
    elif opcode == OpCode.OP_MATMUL:
        B = self.stack.pop()
        A = self.stack.pop()
        self.stack.push(A.matmul(B)) # Contiguous memory tensor product
```

---

## 5. Phase 06: Universal Python Polyglot Bridge

The Python Bridge (`eralang/bridge_python.py`) uses dynamic CPython introspection:
1. When parsing `import python:torch as torch`, the runtime imports the module from host Python.
2. EraLang dynamically generates lightweight proxy descriptors (`PyObjectRef`).
3. Calling `torch.sin(tensor)` converts native EraLang primitive arrays into Python types, dispatches the call into CPython, and wraps output arrays back into EraLang `Tensor` instances seamlessly.

---

## 6. Phase 07: Ahead-Of-Time (AOT) C Transpilation

When running `era build --native main.era`:
1. The AST is mapped directly to ANSI C equivalents via `eralang/c_transpiler.py`.
2. Standard C runtime headers (`stdio.h`, `stdlib.h`, `math.h`, `string.h`) and EraLang's embedded GC runtime are prepended.
3. Invokes the host machine compiler (`gcc`, `clang`, or `cl.exe`) to emit a standalone machine binary (`.exe` / `.elf`) with **zero dependencies on Python**.
