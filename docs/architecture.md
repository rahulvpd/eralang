# 🧠 EraLang Compiler & VM Architecture

EraLang is structured into five distinct phases, allowing either direct interpreted execution, stack-based bytecode evaluation, or ahead-of-time C transpilation.

---

## 🏛️ Compiler Pipeline

```
 Source (.era) ──► Lexer ──► Pratt Parser ──► TypeChecker ──► AST
                                                               │
               ┌───────────────────────────────────────────────┼──────────────────────────────┐
               ▼                                               ▼                              ▼
     [Tree-Walk Evaluator]                           [Bytecode Compiler]             [Native C Transpiler]
   (Interactive & Scripting)                        (High-Performance VM)         (Static Binary Compilation)
```

1. **Lexical Scanner (`eralang/lexer.py`):**
   * Tokenizes source text while preserving exact file names, line numbers, and column offsets.
   * Tolerant of UTF-8 Byte Order Marks (BOM) and multi-line strings.
2. **Recursive Descent Pratt Parser (`eralang/parser.py`):**
   * Uses Pratt parsing for operator precedence (`@` matrix multiplication, logical operators, comparisons).
   * Generates a strongly-typed Abstract Syntax Tree (AST) defined in `eralang/ast_nodes.py`.
3. **Static Typechecker (`eralang/typechecker.py`):**
   * Verifies exhaustive matching on `Option<T>`, `Result<T, E>`, and user-defined `Enum` variants.
   * Prevents unchecked dereferences and invalid reassignments to immutable `let` bindings.
4. **Bytecode Compiler & Virtual Machine (`eralang/compiler.py`, `eralang/vm.py`):**
   * Compiles AST nodes into compact bytecode instruction chunks (`OpCode`).
   * Executes inside a high-speed stack-based VM with a constant pool and scoped variable frames.
5. **Native C Transpiler (`eralang/c_transpiler.py`):**
   * Transpiles EraLang constructs directly to ANSI C code.
   * Involves `gcc` / `clang` / `msvc` to emit standalone native machine binaries (`era build --native`).
