"""
EraLang Interactive REPL (Read-Eval-Print Loop)
"""
import sys
from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .typechecker import TypeChecker
from .evaluator import Evaluator
from .diagnostics import DiagnosticError
from .values import EraOption


def start_repl():
    evaluator = Evaluator(filename="<repl>")

    print("\033[94m" + "=" * 65 + "\033[0m")
    print("\033[92m  🌟 EraLang v2.0.0 Interactive REPL (AI-Native & Pitfall-Proof)\033[0m")
    print("  Type ':help' for commands, ':exit' to quit.")
    print("\033[94m" + "=" * 65 + "\033[0m\n")

    multiline_buffer = []

    while True:
        try:
            prompt = "... " if multiline_buffer else "\033[96mera>\033[0m "
            line = input(prompt)

            # Check special REPL commands
            trimmed = line.strip()
            if not multiline_buffer:
                if trimmed in (":exit", ":quit", "exit()", "quit()"):
                    print("Goodbye!")
                    break
                if trimmed == ":help":
                    print("\nCommands:")
                    print("  :exit / :quit  - Exit the REPL")
                    print("  :env           - List variables in current scope")
                    print("  :clear         - Clear screen")
                    print("  :help          - Show this help message\n")
                    continue
                if trimmed == ":clear":
                    print("\033[2J\033[H", end="")
                    continue
                if trimmed == ":env":
                    print("\nCurrent Environment Scope:")
                    for k, v in evaluator.global_env.values.items():
                        mut = "var" if evaluator.global_env.mutable_flags.get(k, False) else "let"
                        print(f"  {mut} {k}: {v.type_name()} = {v.to_string()}")
                    print()
                    continue

            multiline_buffer.append(line)
            source = "\n".join(multiline_buffer)

            # Check brace balance for multi-line entry (ignore brackets inside strings/comments)
            def _balance_counts(src: str):
                # Strip string literals and comments to avoid false positives
                import re
                # Remove // comments
                no_line_comments = re.sub(r'//.*', '', src)
                # Remove /* */ block comments
                no_comments = re.sub(r'/\*.*?\*/', '', no_line_comments, flags=re.DOTALL)
                # Remove string literals
                no_strings = re.sub(r'"(?:\\.|[^"\\])*"', '', no_comments)
                return (
                    no_strings.count("{") - no_strings.count("}"),
                    no_strings.count("(") - no_strings.count(")"),
                    no_strings.count("[") - no_strings.count("]")
                )
            open_braces, open_parens, open_brackets = _balance_counts(source)

            if open_braces > 0 or open_parens > 0 or open_brackets > 0:
                continue

            # Complete input received
            multiline_buffer = []

            # 1. Lexing
            lexer = Lexer(source, filename="<repl>")
            tokens = lexer.tokenize()

            # 2. Parsing
            parser = Parser(tokens, filename="<repl>")
            program = parser.parse()

            # 3. Typechecking (fresh checker per input to avoid scope leak)
            typechecker = TypeChecker(source_code=source)
            typechecker.check(program)

            # 4. Evaluation
            evaluator.source_code = source
            result = evaluator.evaluate_program(program)

            if result is not None and not (isinstance(result, EraOption) and not result.is_some):
                print(f"\033[93m=>\033[0m {result.to_string()} \033[90m({result.type_name()})\033[0m")

        except (LexerError, ParserError, DiagnosticError) as e:
            print(e)
            multiline_buffer = []
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
            multiline_buffer = []
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\033[91m[Runtime Error]:\033[0m {str(e)}")
            multiline_buffer = []


if __name__ == "__main__":
    start_repl()
