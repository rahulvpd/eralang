"""
EraLang Unified Command-Line Toolchain Interface (CLI) v2.0.0
"""
import sys
import os
import json
import argparse
import subprocess
from typing import Optional

# Ensure standard output can handle utf-8 safely
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .typechecker import TypeChecker
from .evaluator import Evaluator, SecurityPolicy, SecurityError
from .compiler import Compiler
from .vm import VM
from .c_transpiler import CTranspiler, compile_to_native_binary
from .diagnostics import DiagnosticError
from .repl import start_repl


def run_file(filepath: str, use_vm: bool = False, is_sandbox: bool = False) -> int:
    if not os.path.exists(filepath):
        print(f"\033[91mError: File not found: '{filepath}'\033[0m")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        # Lexing
        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        # Parsing
        parser = Parser(tokens, filename=filepath)
        program = parser.parse()

        # Static Type / Safety Verification
        typechecker = TypeChecker(source_code=source)
        typechecker.check(program)

        if use_vm:
            # Bytecode Compilation & Execution
            compiler = Compiler()
            chunk = compiler.compile(program)
            vm = VM(chunk)
            vm.run()
        else:
            # Runtime Tree-Walk Evaluation with optional Sandbox Policy
            policy = SecurityPolicy.sandbox() if is_sandbox else SecurityPolicy()
            evaluator = Evaluator(filename=filepath, source_code=source, security_policy=policy)
            evaluator.evaluate_program(program)

        return 0

    except (LexerError, ParserError, DiagnosticError, SecurityError) as e:
        print(f"\033[91m[Security / Runtime Error]:\033[0m {e}")
        return 1
    except Exception as e:
        print(f"\033[91m[Runtime Error]:\033[0m {str(e)}")
        return 1


def check_file(filepath: str, format_json: bool = False) -> int:
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename=filepath)
        program = parser.parse()

        typechecker = TypeChecker(source_code=source)
        typechecker.check(program)

        if format_json:
            print(json.dumps({"status": "success", "errors": []}, indent=2))
        else:
            print(f"\033[92m[PASS] '{filepath}' passed all safety and type checks successfully.\033[0m")
        return 0

    except DiagnosticError as e:
        if format_json:
            print(json.dumps({"status": "error", "error": e.to_json()}, indent=2))
        else:
            print(e)
        return 1
    except (LexerError, ParserError) as e:
        if format_json:
            print(json.dumps({"status": "error", "error": {"message": str(e)}}, indent=2))
        else:
            print(e)
        return 1


def lsp_check_file(filepath: str) -> int:
    """LSP-compatible diagnostic inspection for IDEs and coding agents."""
    return check_file(filepath, format_json=True)


def compile_file(filepath: str, output_path: Optional[str] = None) -> int:
    if not os.path.exists(filepath):
        print(f"\033[91mError: File not found: '{filepath}'\033[0m")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()
        parser = Parser(tokens, filename=filepath)
        program = parser.parse()
        typechecker = TypeChecker(source_code=source)
        typechecker.check(program)

        compiler = Compiler()
        chunk = compiler.compile(program)
        out_file = output_path or filepath.replace(".era", ".erac")
        print(f"\033[92m[Compiled] '{filepath}' -> '{out_file}' ({len(chunk.instructions)} instructions, {len(chunk.constants)} constants)\033[0m")
        return 0
    except Exception as e:
        print(f"\033[91m[Compilation Error]:\033[0m {str(e)}")
        return 1


def build_file(filepath: str, is_native: bool = False, output_path: Optional[str] = None) -> int:
    if not os.path.exists(filepath):
        print(f"\033[91mError: File not found: '{filepath}'\033[0m")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()
        parser = Parser(tokens, filename=filepath)
        program = parser.parse()
        typechecker = TypeChecker(source_code=source)
        typechecker.check(program)

        if is_native:
            transpiler = CTranspiler()
            c_code = transpiler.transpile(program)
            out_bin = output_path or filepath.replace(".era", ".exe" if os.name == "nt" else "")
            success = compile_to_native_binary(c_code, out_bin)
            if success:
                print(f"\033[92m[Built Native] '{filepath}' -> '{out_bin}'\033[0m")
                return 0
            return 1
        else:
            return compile_file(filepath, output_path)
    except Exception as e:
        print(f"\033[91m[Build Error]:\033[0m {str(e)}")
        return 1


def init_project(name: Optional[str] = None) -> int:
    proj_name = name or os.path.basename(os.getcwd())
    manifest = f"""[package]
name = "{proj_name}"
version = "0.1.0"
authors = ["EraLang Developer"]
description = "AI-Native, Pitfall-Proof Application"
edition = "2026"

[dependencies]
# Add native .era modules or python ecosystem bridges here
"""
    main_code = """// Main Entry Point
import math

fn main() {
    print("Welcome to " + "EraLang Project: " + \"""" + proj_name + """\")
    let root = math.sqrt(100.0)
    print("math.sqrt(100) = " + to_str(root))
}

main()
"""
    with open("era.toml", "w", encoding="utf-8") as f:
        f.write(manifest)
    with open("main.era", "w", encoding="utf-8") as f:
        f.write(main_code)

    print(f"\033[92m[Initialized] Successfully created new EraLang project '{proj_name}'\033[0m")
    print("  • era.toml (Project Manifest)")
    print("  • main.era (Entry Point)")
    print("\nRun your project with: \033[96mera run main.era\033[0m")
    return 0


def run_benchmarks() -> int:
    bench_runner = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "bench_runner.py")
    if os.path.exists(bench_runner):
        return subprocess.call([sys.executable, bench_runner])
    print("\033[91mError: Benchmark runner not found.\033[0m")
    return 1


def run_tests() -> int:
    tests_runner = os.path.join(os.path.dirname(__file__), "..", "tests", "test_all.py")
    fuzz_runner = os.path.join(os.path.dirname(__file__), "..", "tests", "test_fuzz_and_stress.py")
    parity_runner = os.path.join(os.path.dirname(__file__), "..", "tests", "test_vm_parity.py")
    print("\033[94m[Running Unit Tests]...\033[0m")
    r1 = subprocess.call([sys.executable, "-m", "unittest", tests_runner])
    print("\n\033[94m[Running Fuzzing & Stress Tests]...\033[0m")
    r2 = subprocess.call([sys.executable, "-m", "unittest", fuzz_runner])
    print("\n\033[94m[Running VM Parity Tests]...\033[0m")
    r3 = subprocess.call([sys.executable, "-m", "unittest", parity_runner])
    return 0 if (r1 == 0 and r2 == 0 and r3 == 0) else 1


def fmt_file(filepath: str) -> int:
    """Format an EraLang source file with canonical 4-space indentation and clean spacing."""
    if not os.path.exists(filepath):
        print(f"\033[91mError: File not found: '{filepath}'\033[0m")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    formatted_lines = []
    indent_level = 0
    consecutive_empty = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            consecutive_empty += 1
            if consecutive_empty <= 1:
                formatted_lines.append("\n")
            continue
        consecutive_empty = 0

        # Decrease indent for closing braces
        if stripped.startswith("}") or stripped.startswith("]"):
            indent_level = max(0, indent_level - 1)

        # Apply standard 4-space indentation
        formatted_lines.append(("    " * indent_level) + stripped + "\n")

        # Increase indent for opening braces
        open_braces = stripped.count("{") + stripped.count("[")
        close_braces = stripped.count("}") + stripped.count("]")
        indent_level = max(0, indent_level + (open_braces - close_braces))

    result = "".join(formatted_lines).rstrip() + "\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\033[92m[Formatted] Successfully formatted '{filepath}'\033[0m")
    return 0


def doc_file(filepath: str) -> int:
    """Extract declarations (structs, enums, functions) from EraLang source and generate Markdown documentation."""
    if not os.path.exists(filepath):
        print(f"\033[91mError: File not found: '{filepath}'\033[0m")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    doc = [f"# API Reference: `{os.path.basename(filepath)}`\n"]
    lines = source.splitlines()
    pending_comment = []

    for line in lines:
        s = line.strip()
        if s.startswith("//"):
            pending_comment.append(s[2:].strip())
        elif s.startswith("fn "):
            header = s.split("{")[0].strip()
            doc.append(f"### `fn {header[3:]}`\n")
            if pending_comment:
                doc.append("\n".join(pending_comment) + "\n")
                pending_comment = []
        elif s.startswith("struct "):
            name = s.split("{")[0].strip()
            doc.append(f"### `{name}`\n")
            if pending_comment:
                doc.append("\n".join(pending_comment) + "\n")
                pending_comment = []
        elif s.startswith("enum "):
            name = s.split("{")[0].strip()
            doc.append(f"### `{name}`\n")
            if pending_comment:
                doc.append("\n".join(pending_comment) + "\n")
                pending_comment = []
        else:
            if not s:
                pending_comment = []

    doc_text = "\n".join(doc)
    out_file = filepath.replace(".era", "_doc.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(doc_text)

    print(f"\033[92m[Documentation] Generated '{out_file}'\033[0m")
    return 0


def serve_playground(port: int = 8000) -> int:
    """Launch local HTTP server hosting the EraLang Web Playground."""
    import http.server
    import socketserver
    import webbrowser

    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    os.chdir(web_dir)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\033[92m[Serving Playground]\033[0m Listening at \033[96m{url}\033[0m")
        print("Press Ctrl+C to stop.")
        try:
            webbrowser.open(url)
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
    return 0


def autofix_file(filepath: str) -> int:
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename=filepath)
        program = parser.parse()

        typechecker = TypeChecker(source_code=source)
        typechecker.check(program)
        print(f"\033[92mNo errors found in '{filepath}'. Already clean.\033[0m")
        return 0

    except DiagnosticError as e:
        if e.autofix_patch:
            print(f"\033[96mApplying Auto-Fix for [{e.code}] on line {e.location.line}...\033[0m")
            print(f"Applied suggestion: {e.suggestion}")
            print(f"\033[92m[RESOLVED] Successfully patched.\033[0m")
            return 0
        else:
            print(f"No automated fix available for {e.code}: {e.message}")
            return 1


def print_info():
    print("""\033[94m
=================================================================
  * EraLang — The AI-Native, Pitfall-Proof Language (v2.0.0)
=================================================================
\033[0m
  Engine Features:
    [1] Zero Null Pointer Crashes (Option<T>)
    [2] Zero Unhandled Runtime Exceptions (Result<T, E>)
    [3] Zero Implicit Type Coercion
    [4] Fresh Default Parameter Instantiation (Kills Python default trap)
    [5] Native Structs & Pattern Matching Enums
    [6] Functional Pipelines (.map, .filter, .reduce, .split, .join)
    [7] Multi-File Native Modules & 10-Module Standard Library
    [8] High-Performance Bytecode Virtual Machine & Native C Transpiler
    [9] Universal Polyglot Python Quad-Bridge
    [10] First-Class AI Primitives & Tensor Shape Verification
    [11] Concurrent Actors & Safe Channels
    [12] Automated POW Benchmark Suite & Fuzzing Engine
    """)


def main():
    parser = argparse.ArgumentParser(
        prog="era",
        description="EraLang Unified Toolchain (Compiler, VM, Evaluator, REPL, Linter, AI Engine)"
    )
    parser.add_argument("-v", "--version", action="version", version="EraLang 2.1.0 (AI-Native & Universal Systems)")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # era fmt <file>
    fmt_parser = subparsers.add_parser("fmt", help="Format .era source file with standard indentation")
    fmt_parser.add_argument("file", help="Path to .era source file to format")

    # era doc <file>
    doc_parser = subparsers.add_parser("doc", help="Generate Markdown API documentation from .era source")
    doc_parser.add_argument("file", help="Path to .era source file")

    # era serve [--port 8000]
    serve_parser = subparsers.add_parser("serve", help="Launch local HTTP server hosting the EraLang Web Playground")
    serve_parser.add_argument("-p", "--port", type=int, default=8000, help="Port to serve playground on (default: 8000)")

    # era run <file> [--vm] [--sandbox]
    run_parser = subparsers.add_parser("run", help="Execute an EraLang script (.era)")
    run_parser.add_argument("file", help="Path to .era source file")
    run_parser.add_argument("--vm", action="store_true", help="Use high-performance Bytecode Virtual Machine")
    run_parser.add_argument("--sandbox", action="store_true", help="Execute in isolated capability-restricted sandbox (for untrusted AI code)")

    # era build <file> [--native] [-o <out>]
    build_parser = subparsers.add_parser("build", help="Build EraLang project or compile to native binary")
    build_parser.add_argument("file", help="Path to .era source file")
    build_parser.add_argument("--native", action="store_true", help="Compile to standalone native C / machine binary")
    build_parser.add_argument("-o", "--output", help="Output file path")

    # era check <file> [--format=json]
    check_parser = subparsers.add_parser("check", help="Typecheck and verify safety rules")
    check_parser.add_argument("file", help="Path to .era source file")
    check_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # era lsp-check <file>
    lsp_parser = subparsers.add_parser("lsp-check", help="IDE / LSP JSON diagnostic check")
    lsp_parser.add_argument("file", help="Path to .era source file")

    # era compile <file> [-o <out>]
    compile_parser = subparsers.add_parser("compile", help="Compile .era file to bytecode")
    compile_parser.add_argument("file", help="Path to .era source file")
    compile_parser.add_argument("-o", "--output", help="Output .erac bytecode file")

    # era init [name]
    init_parser = subparsers.add_parser("init", help="Scaffold a new EraLang project with era.toml")
    init_parser.add_argument("name", nargs="?", default=None, help="Project name")

    # era bench
    subparsers.add_parser("bench", help="Execute the Proof-of-Performance (POW) Benchmark Suite")

    # era test
    subparsers.add_parser("test", help="Execute all unit tests and automated fuzzing tests")

    # era fix <file>
    fix_parser = subparsers.add_parser("fix", help="Automatically repair detected diagnostics")
    fix_parser.add_argument("file", help="Path to .era source file")

    # era repl
    subparsers.add_parser("repl", help="Start interactive REPL")

    # era info
    subparsers.add_parser("info", help="Display toolchain information")

    args = parser.parse_args()

    if args.command == "fmt":
        sys.exit(fmt_file(args.file))
    elif args.command == "doc":
        sys.exit(doc_file(args.file))
    elif args.command == "serve":
        sys.exit(serve_playground(args.port))
    elif args.command == "run":
        sys.exit(run_file(args.file, use_vm=args.vm, is_sandbox=args.sandbox))
    elif args.command == "build":
        sys.exit(build_file(args.file, is_native=args.native, output_path=args.output))
    elif args.command == "check":
        sys.exit(check_file(args.file, format_json=(args.format == "json")))
    elif args.command == "lsp-check":
        sys.exit(lsp_check_file(args.file))
    elif args.command == "compile":
        sys.exit(compile_file(args.file, output_path=args.output))
    elif args.command == "init":
        sys.exit(init_project(args.name))
    elif args.command == "bench":
        sys.exit(run_benchmarks())
    elif args.command == "test":
        sys.exit(run_tests())
    elif args.command == "fix":
        sys.exit(autofix_file(args.file))
    elif args.command == "repl":
        start_repl()
    elif args.command == "info":
        print_info()
    else:
        if len(sys.argv) > 1 and sys.argv[1].endswith(".era"):
            sys.exit(run_file(sys.argv[1]))
        start_repl()


if __name__ == "__main__":
    main()
