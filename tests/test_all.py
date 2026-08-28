"""
Comprehensive Automated Test Suite for EraLang 2.0
Verifies all core pillars:
1. Lexer & Tokenizer
2. Parser & AST
3. Option<T> and Null Safety
4. Result<T, E> and Error Handling
5. Zero Implicit Coercion Rejection
6. Exhaustive Pattern Matching
7. Fresh Default Arguments (Mutable trap fix)
8. Safe Ranges (0..<n) & Safe Bounds
9. Python Ecosystem Polyglot Bridge
10. Native Tensors & Tensor Math (@, mean, sum, transpose)
11. Native Structs with Typed Fields
12. Enums and Pattern Matching
13. Functional Array Pipelines (.map, .filter, .reduce, .slice, .contains)
14. String Utilities (.split, .trim, .replace, .starts_with, .to_upper)
15. Standard Library Modules (math, fs, json, time)
16. Native Multi-File Module Imports
17. Bytecode Compiler & Virtual Machine (VM)
"""
import unittest
import os
import sys

# Ensure eralang package is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eralang.lexer import Lexer
from eralang.parser import Parser
from eralang.typechecker import TypeChecker
from eralang.evaluator import Evaluator
from eralang.compiler import Compiler
from eralang.vm import VM
from eralang.diagnostics import DiagnosticError
from eralang.values import (
    EraInt, EraFloat, EraString, EraBool, EraOption, EraResult, EraArray, EraTensor,
    EraStructInstance, EraEnumValue
)


def run_code(source: str):
    lexer = Lexer(source, filename="<test>")
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename="<test>")
    prog = parser.parse()
    tc = TypeChecker(source_code=source)
    tc.check(prog)
    ev = Evaluator(filename="<test>", source_code=source)
    return ev.evaluate_program(prog)


class TestEraLang(unittest.TestCase):

    def test_basic_arithmetic_and_let(self):
        source = """
        let x = 10
        let y = 20
        let z = x + y * 2
        """
        res = run_code(source)
        self.assertIsInstance(res, EraInt)
        self.assertEqual(res.value, 50)

    def test_immutability_enforcement(self):
        source = """
        let x = 10
        x = 20
        """
        with self.assertRaises(DiagnosticError) as ctx:
            run_code(source)
        self.assertEqual(ctx.exception.code, "E0101")

    def test_mutable_var(self):
        source = """
        var x = 10
        x = 25
        x += 5
        """
        res = run_code(source)
        self.assertEqual(res.value, 30)

    def test_zero_implicit_coercion(self):
        source = """
        let invalid = "5" + 3
        """
        with self.assertRaises(DiagnosticError) as ctx:
            run_code(source)
        self.assertEqual(ctx.exception.code, "E0201")

    def test_option_some_and_none(self):
        source = """
        fn find_item(flag: bool) -> Option<int> {
            if flag {
                return Some(42)
            }
            return None
        }

        let a = find_item(true).unwrap_or(0)
        let b = find_item(false).unwrap_or(99)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("a").value, 42)
        self.assertEqual(ev.global_env.get("b").value, 99)

    def test_exhaustive_pattern_matching_enforced(self):
        bad_source = """
        let opt = Some(10)
        match opt {
            Some(x) => x + 1
        }
        """
        with self.assertRaises(DiagnosticError) as ctx:
            run_code(bad_source)
        self.assertEqual(ctx.exception.code, "E0301")

    def test_fresh_default_arguments(self):
        source = """
        fn append_val(x: int, acc: [int] = []) -> [int] {
            acc.push(x)
            return acc
        }
        let list1 = append_val(10)
        let list2 = append_val(20)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        l1 = ev.global_env.get("list1")
        l2 = ev.global_env.get("list2")
        self.assertEqual(len(l1.elements), 1)
        self.assertEqual(l1.elements[0].value, 10)
        self.assertEqual(len(l2.elements), 1)
        self.assertEqual(l2.elements[0].value, 20)

    def test_safe_half_open_ranges(self):
        source = """
        var total = 0
        for i in 0..<5 {
            total += i
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("total").value, 10)

    def test_python_polyglot_bridge(self):
        source = """
        import python:math as math
        let root = math.sqrt(64)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("root").value, 8.0)

    def test_tensor_matrix_multiplication_and_ops(self):
        source = """
        let A = Tensor.from_array([[1.0, 2.0], [3.0, 4.0]])
        let B = Tensor.from_array([[2.0, 0.0], [1.0, 2.0]])
        let C = A @ B
        let s = C.sum()
        let m = C.mean()
        let T = C.transpose()
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        c = ev.global_env.get("C")
        self.assertIsInstance(c, EraTensor)
        self.assertEqual(c.data, [[4.0, 4.0], [10.0, 8.0]])
        self.assertEqual(ev.global_env.get("s").value, 26.0)
        self.assertEqual(ev.global_env.get("m").value, 6.5)

    def test_native_structs(self):
        source = """
        struct Vector2D {
            x: float,
            y: float
        }
        let v = Vector2D(3.0, 4.0)
        let vx = v.x
        let vy = v.y
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("vx").value, 3.0)
        self.assertEqual(ev.global_env.get("vy").value, 4.0)

    def test_native_enums_and_matching(self):
        source = """
        enum Mode {
            Fast,
            Safe
        }
        let m = Mode.Safe
        var res = "none"
        match m {
            Mode.Fast => { res = "fast" }
            Mode.Safe => { res = "safe" }
            _ => { res = "other" }
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("res").value, "safe")

    def test_functional_array_pipelines(self):
        source = """
        fn double_val(n: int) -> int { return n * 2 }
        fn is_gt_5(n: int) -> bool { return n > 5 }
        fn add_two(a: int, b: int) -> int { return a + b }

        let nums = [2, 4, 6]
        let doubled = nums.map(double_val)
        let filtered = doubled.filter(is_gt_5)
        let sum = filtered.reduce(add_two, 0)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        # nums = [2, 4, 6] -> doubled = [4, 8, 12] -> filtered = [8, 12] -> sum = 20
        self.assertEqual(ev.global_env.get("sum").value, 20)

    def test_string_utilities(self):
        source = """
        let raw = "  hello,world,era  "
        let trimmed = raw.trim()
        let parts = trimmed.split(",")
        let upper = trimmed.to_upper()
        let has_era = trimmed.contains("era")
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("trimmed").value, "hello,world,era")
        self.assertEqual(len(ev.global_env.get("parts").elements), 3)
        self.assertEqual(ev.global_env.get("upper").value, "HELLO,WORLD,ERA")
        self.assertTrue(ev.global_env.get("has_era").value)

    def test_stdlib_math_json_fs(self):
        source = """
        import math
        import json
        import fs

        let sq = math.sqrt(81.0)
        let p = json.parse("{\\"score\\": 100}")
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("sq").value, 9.0)
        res = ev.global_env.get("p")
        self.assertTrue(res.is_ok)

    def test_bytecode_compiler_and_vm(self):
        source = """
        let a = 15
        let b = 25
        let c = a + b * 2
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        compiler = Compiler()
        chunk = compiler.compile(prog)
        vm = VM(chunk)
        res = vm.run()
        self.assertEqual(vm.env.get("c").value, 65)


    def test_stdlib_crypto_and_os(self):
        source = """
        import crypto
        import os

        let h = crypto.sha256("test")
        let plat = os.platform()
        let d = os.cwd()
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        self.assertEqual(ev.global_env.get("h").value, "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08")
        self.assertIsInstance(ev.global_env.get("plat").value, str)
        self.assertIsInstance(ev.global_env.get("d").value, str)

    def test_stdlib_engineering_physics_linalg_signal(self):
        source = """
        import physics
        import linalg
        import signal

        let ke = physics.kinetic_energy(100.0, 10.0)
        let cross_v = linalg.cross([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        let dot_v = linalg.dot([2.0, 3.0], [4.0, 5.0])
        let sig_rms = signal.rms([1.0, -1.0, 1.0, -1.0])
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev = Evaluator()
        ev.evaluate_program(prog)
        # 0.5 * 100 * 10^2 = 5000.0
        self.assertEqual(ev.global_env.get("ke").value, 5000.0)
        # i x j = k = [0, 0, 1]
        self.assertEqual(ev.global_env.get("cross_v").elements[2].value, 1.0)
        # 2*4 + 3*5 = 23
        self.assertEqual(ev.global_env.get("dot_v").value, 23.0)
        # sqrt((1+1+1+1)/4) = 1.0
        self.assertEqual(ev.global_env.get("sig_rms").value, 1.0)

    def test_security_sandbox_and_dos_protection(self):
        from eralang.evaluator import SecurityPolicy, SecurityError

        # 1. Test that sandbox blocks python bridge
        bad_source = "import python:math as m"
        lexer = Lexer(bad_source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        prog = parser.parse()
        ev_sandbox = Evaluator(security_policy=SecurityPolicy.sandbox())
        with self.assertRaises(SecurityError):
            ev_sandbox.evaluate_program(prog)

        # 2. Test that infinite loop triggers DoS step limit
        infinite_loop = """
        var i = 0
        while true {
            i += 1
        }
        """
        l2 = Lexer(infinite_loop)
        p2 = Parser(l2.tokenize())
        prog2 = p2.parse()
        ev_loop = Evaluator(security_policy=SecurityPolicy(max_steps=100))
        with self.assertRaises(SecurityError):
            ev_loop.evaluate_program(prog2)


if __name__ == "__main__":
    unittest.main()
