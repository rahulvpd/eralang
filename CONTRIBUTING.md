# 🤝 Contributing to EraLang

First off, thank you for considering contributing to EraLang! EraLang is an open-source, community-driven language designed to eliminate silent bugs and make AI, edge, and universal systems programming safer and faster.

---

## 🛠️ Development Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/rahulvpd/eralang.git
   cd eralang
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install in Editable Mode with Dev Dependencies:**
   ```bash
   pip install -e ".[dev,all]"
   ```

4. **Verify Tests:**
   ```bash
   python era.py test
   ```

---

## 🧪 Testing Guidelines

Before opening a pull request, ensure all tests pass:

```bash
# Run core unit and fuzzing tests
python era.py test

# Run VM parity tests
python -m unittest tests/test_vm_parity.py

# Run benchmarks smoke test
python era.py bench
```

If you add a new language construct, built-in function, or standard library method:
1. Add corresponding unit test cases in `tests/test_all.py`.
2. If applicable to the VM, add parity verification in `tests/test_vm_parity.py`.
3. Add an example script under `examples/`.

---

## 📁 Code Organization

* **`eralang/lexer.py`**: Token scanner, whitespace handling, source spans.
* **`eralang/parser.py`**: Pratt parser handling operator precedence, AST creation.
* **`eralang/typechecker.py`**: Static analysis, exhaustiveness checking, type validation.
* **`eralang/evaluator.py`**: Tree-walking runtime interpreter.
* **`eralang/compiler.py`**: Bytecode compiler, OpCodes, constant pool.
* **`eralang/vm.py`**: Stack-based bytecode virtual machine.
* **`eralang/stdlib.py`**: Pure Standard Library implementations (`math`, `linalg`, `physics`, `signal`, etc.).
* **`eralang/bridge_python.py`**: Polyglot bridge for importing Python packages seamlessly.

---

## 📜 Pull Request Process

1. Fork the repo and create a descriptive branch: `git checkout -b feature/my-cool-feature`.
2. Follow standard PEP 8 naming conventions in Python.
3. Commit with concise semantic messages (e.g. `feat: add matrix inverse to linalg stdlib`).
4. Ensure your PR passes all checks in GitHub Actions CI.
