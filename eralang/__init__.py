"""
EraLang — The AI-Native, Pitfall-Proof Programming Language
Official Python SDK & Agent Execution Sandbox (v2.0.0)
"""
from typing import Any, Optional, Dict
from .token import Token, TokenType, SourceLocation
from .lexer import Lexer, LexerError
from .ast_nodes import Program
from .parser import Parser, ParserError
from .typechecker import TypeChecker
from .evaluator import Evaluator
from .compiler import Compiler
from .vm import VM
from .c_transpiler import CTranspiler, compile_to_native_binary
from .diagnostics import DiagnosticError
from .ai_runtime import AIRuntime
from .bridge_python import load_python_module

__version__ = "2.0.0"
__author__ = "EraLang Core Team & Community"


def run(source_code: str, use_vm: bool = False) -> Any:
    """
    Execute EraLang code in an isolated, safe execution sandbox.
    Ideal for AI Coding Agents, LangChain tools, and embedded scripting.
    """
    lexer = Lexer(source_code, filename="<eval>")
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename="<eval>")
    program = parser.parse()

    typechecker = TypeChecker(source_code=source_code)
    typechecker.check(program)

    if use_vm:
        compiler = Compiler()
        chunk = compiler.compile(program)
        vm = VM(chunk)
        return vm.run()
    else:
        evaluator = Evaluator(filename="<eval>", source_code=source_code)
        return evaluator.evaluate_program(program)


def check(source_code: str) -> Dict[str, Any]:
    """
    Statically typecheck EraLang code and return validation status without running.
    """
    try:
        lexer = Lexer(source_code, filename="<check>")
        tokens = lexer.tokenize()
        parser = Parser(tokens, filename="<check>")
        program = parser.parse()

        typechecker = TypeChecker(source_code=source_code)
        typechecker.check(program)
        return {"valid": True, "errors": []}
    except DiagnosticError as e:
        return {"valid": False, "code": e.code, "message": e.message, "suggestion": e.suggestion}
    except (LexerError, ParserError) as e:
        return {"valid": False, "message": str(e)}


def to_c(source_code: str) -> str:
    """
    Transpile EraLang source code directly to ANSI C99.
    """
    lexer = Lexer(source_code, filename="<transpile>")
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename="<transpile>")
    program = parser.parse()
    transpiler = CTranspiler()
    return transpiler.transpile(program)
