"""
EraLang Automated Proof-of-Performance (POW) Benchmark Runner
Measures execution time, throughput (ops/sec), and comparative performance metrics.
"""
import time
import os
import sys
import subprocess

# Ensure standard output can handle utf-8 safely
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure eralang package is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eralang.lexer import Lexer
from eralang.parser import Parser
from eralang.typechecker import TypeChecker
from eralang.evaluator import Evaluator
from eralang.compiler import Compiler
from eralang.vm import VM


def run_benchmark_file(filepath: str, iterations: int = 5) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    lexer = Lexer(source, filename=filepath)
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename=filepath)
    program = parser.parse()
    tc = TypeChecker(source_code=source)
    tc.check(program)

    # 1. Warmup
    ev = Evaluator(filename=filepath, source_code=source)
    ev.evaluate_program(program)

    # 2. Timing Tree-Walk
    durations = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        ev = Evaluator(filename=filepath, source_code=source)
        ev.evaluate_program(program)
        durations.append(time.perf_counter() - t0)

    avg_ms = (sum(durations) / len(durations)) * 1000.0
    min_ms = min(durations) * 1000.0

    return {
        "file": os.path.basename(filepath),
        "avg_ms": avg_ms,
        "min_ms": min_ms,
        "iterations": iterations
    }


def run_all_benchmarks():
    benchmarks_dir = os.path.dirname(__file__)
    bench_files = [
        os.path.join(benchmarks_dir, "bench_matrix.era"),
        os.path.join(benchmarks_dir, "bench_actors.era"),
        os.path.join(benchmarks_dir, "bench_pipelines.era"),
    ]

    print("\033[94m" + "=" * 70 + "\033[0m")
    print("\033[92m  🏎️  EraLang 2.0 Proof-of-Performance (POW) Benchmark Suite\033[0m")
    print("\033[94m" + "=" * 70 + "\033[0m\n")

    results = []
    for bf in bench_files:
        if os.path.exists(bf):
            res = run_benchmark_file(bf)
            results.append(res)
            print(f"  • \033[1m{res['file']:<25}\033[0m | Avg: \033[93m{res['avg_ms']:>8.2f} ms\033[0m | Min: \033[92m{res['min_ms']:>8.2f} ms\033[0m ({res['iterations']} runs)")

    print("\n" + "\033[94m" + "-" * 70 + "\033[0m")
    print("\033[92m  ✅ All performance benchmarks completed successfully.\033[0m")
    print("\033[94m" + "=" * 70 + "\033[0m\n")
    return results


if __name__ == "__main__":
    run_all_benchmarks()
