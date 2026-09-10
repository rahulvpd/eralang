# 🌟 EraLang: Documentation Overview

> **Version 2.1.0** — The AI-Native, Pitfall-Proof Programming Language for Scientific & Universal Systems.

EraLang was designed from the ground up to eliminate the root causes of over 80% of production and AI-generated bugs while preserving developer agility and providing first-class scientific computing primitives.

---

## 📚 Documentation Sections

| Guide | Description |
| :--- | :--- |
| [**🚀 Getting Started**](getting-started.md) | Installation, CLI commands, REPL usage, and scaffolding your first project with `era init`. |
| [**📖 Language Tour**](language-tour.md) | Comprehensive syntax guide: Variables, `Option<T>`, `Result<T, E>`, Structs, Enums, Pattern Matching, and Pipelines. |
| [**🔬 Standard Library Reference**](stdlib-reference.md) | Complete API reference for all 10 pure standard library modules (`math`, `linalg`, `physics`, `signal`, `fs`, `json`, `time`, `crypto`, `http`, `os`). |
| [**🐍 Universal Python Bridge**](python-bridge.md) | Zero-boilerplate polyglot interoperability with PyTorch, NumPy, Pandas, Scikit-Learn, and the PyPI ecosystem. |
| [**🧠 Compiler & VM Architecture**](architecture.md) | Deep-dive into the Pratt Parser, Static Typechecker, Stack-based Bytecode VM, and Native C Transpiler. |

---

## 🛡️ Core Safety Guarantees

```
                           ERAWALL SAFETY PIPELINE
                           
       Source Code (.era) ──► Lexer (Span Tracking) ──► Pratt Parser (Rich AST)
                                                               │
                                  ┌────────────────────────────┴────────────────────────────┐
                                  ▼                                                         ▼
                       [Static Verification]                                     [Runtime Enforcement]
                       • Zero Nulls (Option<T>)                                   • No Implicit Coercion
                       • Exhaustive Pattern Matching                             • Bounds-checked Collections
                       • Fresh Default Instantiations                            • Safe Signal & Matrix Ops
```

1. **Zero Null Pointers:** There is no `null`, `nil`, or `NoneType`. All optional data is represented via `Option<T>` (`Some(v)` or `None`). Unchecked dereferencing triggers compiler diagnostics.
2. **Zero Silent Exceptions:** Operations that can fail return `Result<T, E>` (`Ok(v)` or `Err(e)`). Handlers must exhaustively match or safely unwrap with defaults.
3. **Zero Implicit Type Coercion:** Strings and numbers never silently concatenate or coerce (`"5" + 3` is a compile error, not `"53"` or `8`).
4. **No Mutable Default Traps:** Function defaults are re-instantiated fresh on every invocation, eliminating the famous Python mutable default argument trap.
5. **Universal Polyglot Bridge:** Instant access to all 500,000+ Python packages via `import python:torch as torch` without C-bindings boilerplate.
