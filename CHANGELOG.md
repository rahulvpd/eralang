# 📜 EraLang Changelog

All notable changes to EraLang are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-09-10

### Added
- **Interactive Web Playground with Pyodide Wasm Engine**: Full client-side execution in the browser with real AST and VM evaluations without server dependencies.
- **`era fmt` Command**: Automatic syntax indentation and code formatter for `.era` source files.
- **`era doc` Command**: Automated Markdown API documentation generator from EraLang declarations.
- **`era serve` Command**: Built-in HTTP static server for local playground testing.
- **GitHub Actions CI/CD Matrix**: Continuous integration running tests on Python 3.9–3.12 across Linux, macOS, and Windows.
- **Automated PyPI Release Workflow**: Seamless publishing of source distributions and wheels to PyPI.
- **GitHub Pages Workflow**: Automated deployment of the `web/` playground on pushes to `main`.
- **Docker & DevContainer Support**: Multi-stage `Dockerfile` and `.devcontainer/devcontainer.json` for 1-click cloud development.
- **Comprehensive Documentation Suite**: Added `docs/` covering Language Tour, Standard Library API reference, Python Bridge, and Compiler Architecture.
- **Community Standards**: Added `LICENSE` (MIT), `CONTRIBUTING.md`, issue templates, PR template, and Dependabot.

### Fixed
- Included `test_vm_parity.py` in the unified `era test` test runner.
- Removed tracked `.pyc` compiled bytecode cache files from Git index and added comprehensive `.gitignore`.

---

## [2.0.0] - Initial Production Architecture

### Added
- Core **Lexer**, recursive descent **Pratt Parser**, and static **TypeChecker**.
- First-class **`Option<T>`** (`Some`/`None`) and **`Result<T, E>`** (`Ok`/`Err`).
- Stack-based **Bytecode Virtual Machine (VM)** and Optimizing Compiler.
- Native **C Transpiler** (`era build --native`).
- **Universal Polyglot Bridge** to Python (`import python:<pkg>`).
- 10-Module **Scientific Standard Library** (`math`, `linalg`, `physics`, `signal`, `fs`, `json`, `time`, `crypto`, `http`, `os`).
- First-class **Tensor** support with `@` matrix multiplication operator.
- Concurrent **Actors** and buffered **Channels** (`Chan`).
- Automated POW benchmark suite (`era bench`).
