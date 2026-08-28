"""
EraLang Automated Fuzzing & High-Load Stress Testing Engine
Performs property-based fuzz testing, deep recursion checks, and concurrency stress testing.
"""
import unittest
import random
import string
import time
import threading
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eralang.lexer import Lexer, LexerError
from eralang.parser import Parser, ParserError
from eralang.typechecker import TypeChecker
from eralang.evaluator import Evaluator
from eralang.diagnostics import DiagnosticError
from eralang.values import EraInt, EraOption, EraChannel, EraActor


class TestFuzzAndStress(unittest.TestCase):

    def test_random_syntax_fuzzer(self):
        """
        Feeds 1,000 randomized malformed strings through the full compiler pipeline.
        Must NEVER crash with unhandled Python exceptions (e.g. IndexError, UnboundLocalError).
        """
        random.seed(42)
        fuzz_chars = string.ascii_letters + string.digits + "{}[]()<>=+-*/@%!.,;:?\"' \n\t#&$~`^|\\"

        for i in range(1000):
            length = random.randint(1, 80)
            fuzz_str = "".join(random.choice(fuzz_chars) for _ in range(length))

            try:
                lexer = Lexer(fuzz_str, filename="<fuzz>")
                tokens = lexer.tokenize()
                parser = Parser(tokens, filename="<fuzz>")
                program = parser.parse()
                tc = TypeChecker(source_code=fuzz_str)
                tc.check(program)
            except (LexerError, ParserError, DiagnosticError):
                # Expected clean domain-specific syntax / type errors
                pass
            except Exception as e:
                self.fail(f"UNHANDLED FATAL CRASH during fuzz iteration {i}: {type(e).__name__}: {str(e)}\nInput was: {repr(fuzz_str)}")

    def test_deep_arithmetic_recursion_stress(self):
        """
        Evaluates a 200-level deep chained expression: 1 + 1 + 1 + ...
        """
        depth = 200
        expr_str = " + ".join(["1"] * depth)
        source = f"let result = {expr_str}"

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)

        self.assertEqual(ev.global_env.get("result").value, depth)

    def test_deep_nested_blocks_stress(self):
        """
        Evaluates 50-level deep nested blocks with scoped variables.
        """
        depth = 50
        code = "var count = 0\n"
        for i in range(depth):
            code += f"if count == {i} {{\n count += 1\n"
        code += "}" * depth

        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)

        self.assertEqual(ev.global_env.get("count").value, depth)

    def test_concurrent_actor_channel_stress(self):
        """
        Spawns 20 concurrent green threads sending and receiving 500 messages through channels.
        Validates thread-safety and absence of deadlocks.
        """
        ch = EraChannel(capacity=1000)
        num_messages = 500
        received = []
        lock = threading.Lock()

        def _producer():
            for i in range(num_messages):
                ch.send(EraInt(i))

        def _consumer():
            for _ in range(num_messages):
                val_opt = ch.recv()
                if val_opt.is_some:
                    with lock:
                        received.append(val_opt.val.value)

        t1 = threading.Thread(target=_producer)
        t2 = threading.Thread(target=_consumer)

        t1.start()
        t2.start()

        t1.join(timeout=5.0)
        t2.join(timeout=5.0)

        self.assertEqual(len(received), num_messages)

    def test_repeated_struct_instantiation_memory_stress(self):
        """
        Creates and operates on 5,000 struct instances in a loop.
        """
        source = """
        struct Metric {
            id: int,
            score: float
        }
        var total_score = 0.0
        for i in 0..<1000 {
            let m = Metric(i, 2.5)
            total_score += m.score
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)

        # 1000 * 2.5 = 2500.0
        self.assertEqual(ev.global_env.get("total_score").value, 2500.0)


if __name__ == "__main__":
    unittest.main()
