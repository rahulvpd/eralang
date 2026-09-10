# 🚀 Getting Started with EraLang

Welcome to EraLang! This guide walks you through installation, CLI commands, and creating your first EraLang project.

---

## 📦 Installation

### Option A: Install from PyPI (Recommended)
```bash
pip install --upgrade eralang
```

### Option B: Build from Source
```bash
git clone https://github.com/rahulvpd/eralang.git
cd eralang
pip install -e .
```

Verify your installation:
```bash
era --version
# Output: EraLang 2.1.0 (AI-Native & Universal Systems)
```

---

## ⚡ Toolchain Commands

The `era` CLI provides a unified toolchain for building, checking, testing, and formatting:

```bash
# Run a script with tree-walk interpreter
era run main.era

# Run with high-performance Bytecode VM
era run --vm main.era

# Type-check and verify safety rules without running
era check main.era

# Format your source code (4-space indentation)
era fmt main.era

# Generate Markdown API documentation
era doc main.era

# Scaffold a new project
era init my_project

# Compile to standalone bytecode (.erac)
era compile main.era -o main.erac

# Compile to native C / machine binary
era build main.era --native -o my_app

# Run all unit tests, fuzzing, and VM parity tests
era test

# Run proof-of-performance benchmarks
era bench

# Launch local interactive Web Playground
era serve --port 8000

# Start the interactive REPL
era repl
```

---

## 📝 Your First Program: `hello.era`

Create a file named `hello.era`:

```rust
// hello.era
import math

fn greet(name: string) {
    print("Welcome to EraLang, " + name + "!")
}

greet("Developer")

let radius = 5.0
let area = math.pi * radius * radius
print("Circle area: " + to_str(area))
```

Run it:
```bash
era run hello.era
```

Output:
```text
Welcome to EraLang, Developer!
Circle area: 78.53981633974483
```
