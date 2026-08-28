# 🌟 EraLang: The AI-Native, Pitfall-Proof Programming Language

> **Version 2.0.0** | Designed for the AI, Edge, Scientific & Universal Engineering Systems Era.

EraLang is a modern general-purpose programming language engineered specifically to eliminate the most common, silent, and catastrophic software pitfalls at design-time while providing **first-class AI & tensor primitives**, **native Structs & Enums**, **functional data pipelines**, **multi-file native modules**, a **pure 10-module Scientific Standard Library** (`math`, `fs`, `json`, `time`, `crypto`, `http`, `os`, `linalg`, `signal`, `physics`), an **optimizing Bytecode Virtual Machine**, and **zero-boilerplate access to the entire Python ecosystem**.

---

## 🛡️ Core Safety Pillars & Bug Elimination

| Classic Pitfall | Root Cause in Other Languages | EraLang 2.0 Solution |
| :--- | :--- | :--- |
| **Null / None Dereference** | Primitive `null`/`None` everywhere | **No `null`**. First-class `Option<T>` (`Some(v)` / `None`). Direct unchecked access is blocked. |
| **Silent Type Coercion Bugs** | Implicit coercion (e.g. `"5" + 3 == "53"`) | **Zero implicit coercion**. Strict typing with explicit conversion functions (`to_str`, `to_int`). |
| **Unchecked Runtime Exceptions** | Unannounced `throw` / `raise` | **No runtime exceptions**. Explicit `Result<T, E>` (`Ok(v)` / `Err(e)`). Exhaustive match forced. |
| **Off-by-One & Bounds Errors** | Raw index loops (`<= vs <`) | Safe half-open ranges `0..<n`. Out-of-bounds indexing returns `Option<T>`. |
| **Mutable Default Arguments Trap** | Defaults instantiated once at definition (Python trap) | **Fresh default instantiation** evaluated dynamically on each call. |
| **Non-Exhaustive Conditionals** | Unhandled edge cases & missing branches | **Compiler-enforced exhaustive pattern matching** on all variants. |
| **Untyped Ad-Hoc Dictionaries** | Missing struct schema enforcement | **Native Structs & Enums** with field-level typing and pattern matching. |
| **Procedural Boilerplate** | Clunky procedural loops for data transformations | **Functional Method Chaining** (`.map()`, `.filter()`, `.reduce()`, `.split()`, `.trim()`). |
| **Engineering Unit / Math Failures** | Clunky math libraries and lack of native tensors | **Built-in Tensors (`@`), Linear Algebra (`linalg`), DSP (`signal`), & Universal Physics (`physics`)**. |
| **Ecosystem Cold-Start** | New languages lack libraries | **Universal Polyglot Bridge** to Python (`import python:torch as torch`) & Native Modules. |

---

## 🚀 Quickstart & Toolchain Commands

### 1. Execute an EraLang Script
```bash
# Standard tree-walk interpreter
python era.py run examples/14_engineering_physics_and_signals.era

# High-performance Bytecode Virtual Machine
python era.py run --vm examples/01_zero_nulls.era
```

### 2. Scaffold a New Project
```bash
python era.py init my_app
```

### 3. Run Proof-of-Performance (POW) Benchmarks
```bash
python era.py bench
```

### 4. Run Complete Test & Fuzzing Suite
```bash
python era.py test
```

### 5. Start the Interactive REPL
```bash
python era.py repl
```

---

## 📖 Universal Engineering & Language Showcase

### 1. Universal Physics & Kinematics (`physics` & `linalg`)
```rust
import physics
import linalg

let satellite_mass = 1200.0 // kg
let orbit_speed = 7800.0    // m/s

let kinetic_energy = physics.kinetic_energy(satellite_mass, orbit_speed)
let gamma = physics.lorentz_factor(orbit_speed)

// 3D Torque Vector: tau = r x F
let lever_arm = [0.0, 1.5, 0.0]
let force = [100.0, 0.0, 50.0]
let torque = linalg.cross(lever_arm, force)

print("Kinetic Energy (J): " + to_str(kinetic_energy))
print("Torque Vector     : " + to_str(torque))
```

### 2. Digital Signal Processing & Fourier Spectra (`signal`)
```rust
import signal

let time_samples = [0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0]
let spectrum = signal.dft(time_samples)
let rms_power = signal.rms(time_samples)

print("DFT Frequency Spectrum: " + to_str(spectrum))
print("Signal RMS Power      : " + to_str(rms_power))
```

### 3. Native Structs & Pattern Matching Enums
```rust
struct Point {
    x: float,
    y: float
}

enum Status {
    Active,
    Pending,
    Archived
}

let p = Point(10.5, 20.25)
let current_status = Status.Active

match current_status {
    Status.Active => print("System is running in ACTIVE mode.")
    Status.Pending => print("System is PENDING.")
    Status.Archived => print("System is ARCHIVED.")
}
```

### 4. Functional Data Pipelines & Method Chaining
```rust
fn is_even(n: int) -> bool { return (n % 2) == 0 }
fn double_it(n: int) -> int { return n * 2 }
fn add(a: int, b: int) -> int { return a + b }

let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let sum = numbers
    .filter(is_even)
    .map(double_it)
    .reduce(add, 0)

print("Sum of doubled evens: " + to_str(sum)) // 60
```

### 5. Native Tensors & AI Primitives
```rust
let A = Tensor.from_array([[1.0, 2.0], [3.0, 4.0]])
let B = Tensor.from_array([[5.0, 6.0], [7.0, 8.0]])
let C = A @ B

print("Product A @ B:")
print(C)
print("Mean: " + to_str(C.mean()))
print("Transpose: ")
print(C.transpose())
```

---

## 📂 Project Directory Structure

```
C:\Users\HP\Desktop\assistive\eralang\
├── eralang/
│   ├── __init__.py
│   ├── token.py           # Tokens, Keywords, and SourceLocation tracking
│   ├── lexer.py           # Hardened Lexical Scanner with span tracking & BOM tolerance
│   ├── ast_nodes.py       # Rich AST hierarchy (Structs, Enums, Patterns, Statements)
│   ├── parser.py          # Recursive descent Pratt parser
│   ├── typechecker.py     # Static safety & exhaustiveness verifier (E0101, E0201, E0301, E0302)
│   ├── environment.py     # Scoped lexical environment (let vs var immutability)
│   ├── values.py          # Runtime values (Option, Result, Structs, Enums, Tensor, etc.)
│   ├── evaluator.py       # Tree-walk interpreter runtime with module loader
│   ├── stdlib.py          # Pure 10-Module Standard Library (math, fs, json, time, crypto, http, os, linalg, signal, physics)
│   ├── compiler.py        # Optimizing Bytecode Compiler & OpCodes
│   ├── vm.py              # Stack-based Bytecode Virtual Machine
│   ├── bridge_python.py   # Zero-boilerplate Python ecosystem polyglot bridge
│   ├── ai_runtime.py      # AI completions, embeddings, and vector math
│   ├── diagnostics.py     # "Mentor" error formatting & auto-fix suggestions
│   ├── repl.py            # Interactive REPL
│   └── cli.py             # Unified CLI (run, --vm, bench, test, init, compile, lsp-check, check, fix)
├── benchmarks/
│   ├── bench_runner.py    # Automated POW benchmark runner
│   ├── bench_matrix.era   # 50x50 Tensor matrix benchmark
│   ├── bench_actors.era   # 1,000 message channel throughput benchmark
│   └── bench_pipelines.era# 1,000 item pipeline benchmark
├── examples/
│   ├── 01_zero_nulls.era
│   ├── 02_safe_errors.era
│   ├── 03_no_coercion.era
│   ├── 04_fresh_defaults.era
│   ├── 05_safe_ranges.era
│   ├── 06_python_interop.era
│   ├── 07_actors_channels.era
│   ├── 08_ai_tensors.era
│   ├── 09_structs_and_enums.era
│   ├── 10_functional_pipelines.era
│   ├── 11_file_and_json_io.era
│   ├── 12_native_modules.era
│   ├── 13_crypto_and_http.era
│   ├── 14_engineering_physics_and_signals.era
│   └── math_utils.era
├── tests/
│   ├── test_all.py        # Automated unit test suite (18 tests, 100% pass)
│   └── test_fuzz_and_stress.py # Automated fuzzing & concurrency stress suite
├── era.py                 # Cross-platform CLI launcher
├── era.bat                # Windows CLI command launcher
└── README.md
```
