"""
EraLang Tree-Walk Runtime Evaluator
Executes the AST with safety guarantees, fresh defaults, polyglot bridging, and concurrency.
"""
from typing import Any, List, Dict, Optional, Tuple
import os
import threading
import time
from .ast_nodes import (
    Program, Stmt, Expr, Pattern,
    LetStmt, VarStmt, AssignStmt, FnDecl, Param, ReturnStmt,
    ForStmt, WhileStmt, BreakStmt, ContinueStmt, ImportStmt,
    ActorDecl, SpawnStmt, ExprStmt, StructDecl, StructField, EnumDecl,
    LiteralExpr, IdentifierExpr, BinaryExpr, UnaryExpr,
    CallExpr, MemberExpr, IndexExpr, ArrayLitExpr, MapLitExpr,
    OptionLitExpr, ResultLitExpr, RangeExpr, MatchExpr, MatchArm,
    IfExpr, BlockExpr, TensorLitExpr, AICompleteExpr, QuestionExpr,
    LiteralPattern, IdentifierPattern, SomePattern, NonePattern,
    OkPattern, ErrPattern, WildcardPattern, EnumPattern
)
from .token import TokenType, SourceLocation
from .values import (
    EraValue, EraInt, EraFloat, EraString, EraBool, EraOption, EraResult,
    EraArray, EraMap, EraTensor, EraFunction, EraBuiltinFunction,
    EraChannel, EraActor, EraForeignObject,
    EraStructDef, EraStructInstance, EraEnumDef, EraEnumValue
)
from .stdlib import EraStdLibModule, get_stdlib_module, BUILTIN_STDLIB_MODULES
from .environment import Environment, EnvironmentError
from dataclasses import dataclass
from .bridge_python import load_python_module, PythonBridgeModule, to_era_value
from .ai_runtime import AIRuntime
from .diagnostics import DiagnosticError


class SecurityError(Exception):
    """Raised when an operation violates the active SecurityPolicy."""
    pass


@dataclass
class SecurityPolicy:
    allow_fs: bool = True
    allow_net: bool = True
    allow_os: bool = True
    allow_python_bridge: bool = True
    max_steps: int = 1_000_000

    @classmethod
    def sandbox(cls) -> 'SecurityPolicy':
        """Restricted capability-based sandbox for untrusted AI-generated code."""
        return cls(allow_fs=False, allow_net=False, allow_os=False, allow_python_bridge=False, max_steps=50_000)


class ReturnValue(Exception):
    def __init__(self, value: EraValue):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class Evaluator:
    def __init__(self, filename: str = "<stdin>", source_code: Optional[str] = None, security_policy: Optional[SecurityPolicy] = None):
        self.filename = filename
        self.source_code = source_code
        self.security_policy = security_policy or SecurityPolicy()
        self.step_count = 0
        self.global_env = Environment()
        self._init_builtins()

    def _init_builtins(self):
        def _print(*args):
            output = " ".join(a.to_string() for a in args)
            print(output)
            return EraOption.none()

        def _to_str(val: EraValue) -> EraString:
            return EraString(val.to_string())

        def _to_int(val: EraValue) -> EraInt:
            if isinstance(val, (EraInt, EraFloat)):
                return EraInt(int(val.value))
            if isinstance(val, EraString):
                return EraInt(int(val.value))
            if isinstance(val, EraBool):
                return EraInt(1 if val.value else 0)
            return EraInt(0)

        def _to_float(val: EraValue) -> EraFloat:
            if isinstance(val, (EraInt, EraFloat)):
                return EraFloat(float(val.value))
            if isinstance(val, EraString):
                return EraFloat(float(val.value))
            return EraFloat(0.0)

        def _len(val: EraValue) -> EraInt:
            if isinstance(val, EraString):
                return EraInt(len(val.value))
            if isinstance(val, EraArray):
                return EraInt(len(val.elements))
            if isinstance(val, EraMap):
                return EraInt(len(val.entries))
            if isinstance(val, EraTensor):
                return EraInt(val.shape[0] if val.shape else 0)
            return EraInt(0)

        def _type_of(val: EraValue) -> EraString:
            return EraString(val.type_name())

        def _assert(cond: EraValue, msg: EraValue = None):
            if not cond.is_truthy():
                m = msg.to_string() if msg else "Assertion failed"
                raise RuntimeError(f"Assertion Error: {m}")
            return EraBool(True)

        def _sleep(sec: EraValue):
            s = sec.value if isinstance(sec, (EraInt, EraFloat)) else 0.0
            time.sleep(s)
            return EraOption.none()

        def _make_chan(capacity: EraValue = None) -> EraChannel:
            cap = capacity.value if (capacity and isinstance(capacity, EraInt)) else 100
            return EraChannel(capacity=cap)

        self.global_env.define("print", EraBuiltinFunction("print", _print), is_mutable=False)
        self.global_env.define("to_str", EraBuiltinFunction("to_str", _to_str), is_mutable=False)
        self.global_env.define("to_int", EraBuiltinFunction("to_int", _to_int), is_mutable=False)
        self.global_env.define("to_float", EraBuiltinFunction("to_float", _to_float), is_mutable=False)
        self.global_env.define("len", EraBuiltinFunction("len", _len), is_mutable=False)
        self.global_env.define("type_of", EraBuiltinFunction("type_of", _type_of), is_mutable=False)
        self.global_env.define("assert", EraBuiltinFunction("assert", _assert), is_mutable=False)
        self.global_env.define("sleep", EraBuiltinFunction("sleep", _sleep), is_mutable=False)
        self.global_env.define("Chan", EraBuiltinFunction("Chan", _make_chan), is_mutable=False)

    def evaluate_program(self, program: Program) -> Optional[EraValue]:
        result = None
        for stmt in program.statements:
            result = self.eval_stmt(stmt, self.global_env)
        return result

    def _check_step_limit(self):
        self.step_count += 1
        if self.step_count > self.security_policy.max_steps:
            raise SecurityError(
                f"SecurityPolicy: Execution step limit exceeded ({self.security_policy.max_steps} steps). DoS / Infinite Loop Protection triggered."
            )

    def eval_stmt(self, stmt: Stmt, env: Environment) -> Optional[EraValue]:
        self._check_step_limit()
        if isinstance(stmt, LetStmt):
            val = self.eval_expr(stmt.initializer, env)
            env.define(stmt.name, val, is_mutable=False)
            return val

        elif isinstance(stmt, VarStmt):
            val = self.eval_expr(stmt.initializer, env)
            env.define(stmt.name, val, is_mutable=True)
            return val

        elif isinstance(stmt, AssignStmt):
            val = self.eval_expr(stmt.value, env)
            if isinstance(stmt.target, IdentifierExpr):
                if stmt.op.type == TokenType.ASSIGN:
                    env.assign(stmt.target.name, val)
                elif stmt.op.type == TokenType.PLUS_ASSIGN:
                    curr = env.get(stmt.target.name)
                    env.assign(stmt.target.name, self._eval_binary_op(curr, TokenType.PLUS, val, stmt.location))
                elif stmt.op.type == TokenType.MINUS_ASSIGN:
                    curr = env.get(stmt.target.name)
                    env.assign(stmt.target.name, self._eval_binary_op(curr, TokenType.MINUS, val, stmt.location))
                elif stmt.op.type == TokenType.STAR_ASSIGN:
                    curr = env.get(stmt.target.name)
                    env.assign(stmt.target.name, self._eval_binary_op(curr, TokenType.STAR, val, stmt.location))
                elif stmt.op.type == TokenType.SLASH_ASSIGN:
                    curr = env.get(stmt.target.name)
                    env.assign(stmt.target.name, self._eval_binary_op(curr, TokenType.SLASH, val, stmt.location))
                return env.get(stmt.target.name)
            elif isinstance(stmt.target, IndexExpr):
                target_obj = self.eval_expr(stmt.target.target, env)
                idx_val = self.eval_expr(stmt.target.index, env)
                if isinstance(target_obj, EraArray) and isinstance(idx_val, EraInt):
                    if 0 <= idx_val.value < len(target_obj.elements):
                        target_obj.elements[idx_val.value] = val
                    else:
                        raise RuntimeError(f"Index out of bounds on array assignment: index {idx_val.value} (length {len(target_obj.elements)})")
                elif isinstance(target_obj, EraMap) and isinstance(idx_val, EraString):
                    target_obj.entries[idx_val.value] = val
                return val
            else:
                raise RuntimeError("Invalid assignment target")

        elif isinstance(stmt, FnDecl):
            fn_val = EraFunction(
                name=stmt.name,
                params=stmt.params,
                body=stmt.body,
                closure=env,
                capabilities=stmt.capabilities
            )
            env.define(stmt.name, fn_val, is_mutable=False)
            return fn_val

        elif isinstance(stmt, ReturnStmt):
            val = self.eval_expr(stmt.value, env) if stmt.value else EraOption.none()
            raise ReturnValue(val)

        elif isinstance(stmt, ForStmt):
            iterable_val = self.eval_expr(stmt.iterable, env)
            items = []
            if isinstance(iterable_val, (range, list)):
                items = iterable_val
            elif isinstance(iterable_val, EraArray):
                items = iterable_val.elements
            elif isinstance(iterable_val, EraString):
                items = [EraString(c) for c in iterable_val.value]
            elif isinstance(iterable_val, EraMap):
                items = [EraString(k) for k in iterable_val.entries.keys()]
            else:
                raise RuntimeError(f"Value of type '{iterable_val.type_name()}' is not iterable in for-loop")

            for item in items:
                loop_env = Environment(parent=env)
                loop_item = EraInt(item) if isinstance(item, int) else item
                loop_env.define(stmt.var_name, loop_item, is_mutable=False)
                try:
                    self.eval_expr(stmt.body, loop_env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return EraOption.none()

        elif isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.condition, env).is_truthy():
                loop_env = Environment(parent=env)
                try:
                    self.eval_expr(stmt.body, loop_env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return EraOption.none()

        elif isinstance(stmt, BreakStmt):
            raise BreakException()

        elif isinstance(stmt, ContinueStmt):
            raise ContinueException()

        elif isinstance(stmt, ImportStmt):
            alias = stmt.alias or stmt.module_path.split("/")[-1].split(".")[0]
            if stmt.kind == "python":
                if not self.security_policy.allow_python_bridge:
                    raise SecurityError("SecurityPolicy: Python ecosystem bridge is disabled in sandbox mode.")
                mod = load_python_module(stmt.module_path)
                env.define(alias, mod, is_mutable=False)
                return mod
            elif stmt.module_path in BUILTIN_STDLIB_MODULES:
                if stmt.module_path == "fs" and not self.security_policy.allow_fs:
                    raise SecurityError("SecurityPolicy: Filesystem (fs) module is disabled in sandbox mode.")
                if stmt.module_path == "http" and not self.security_policy.allow_net:
                    raise SecurityError("SecurityPolicy: Network (http) module is disabled in sandbox mode.")
                if stmt.module_path == "os" and not self.security_policy.allow_os:
                    raise SecurityError("SecurityPolicy: Operating System (os) module is disabled in sandbox mode.")
                mod_opt = get_stdlib_module(stmt.module_path)
                if mod_opt.is_some:
                    env.define(alias, mod_opt.val, is_mutable=False)
                    return mod_opt.val

            # Otherwise, resolve as native .era module
            mod_file = stmt.module_path
            if not mod_file.endswith(".era"):
                mod_file += ".era"

            current_dir = os.path.dirname(self.filename) if self.filename and self.filename not in ("<stdin>", "<test>") else os.getcwd()
            resolved_path = os.path.normpath(os.path.join(current_dir, mod_file))
            if not os.path.exists(resolved_path):
                resolved_path = os.path.normpath(os.path.join(os.getcwd(), mod_file))

            if not os.path.exists(resolved_path):
                raise RuntimeError(f"Could not import module '{stmt.module_path}': file '{resolved_path}' not found")

            with open(resolved_path, "r", encoding="utf-8") as f:
                mod_source = f.read()

            from .lexer import Lexer
            from .parser import Parser
            from .typechecker import TypeChecker

            l = Lexer(mod_source, filename=resolved_path)
            t = l.tokenize()
            p = Parser(t, filename=resolved_path)
            ast = p.parse()
            tc = TypeChecker(source_code=mod_source)
            tc.check(ast)

            mod_eval = Evaluator(filename=resolved_path, source_code=mod_source)
            mod_eval.evaluate_program(ast)

            exports = dict(mod_eval.global_env.values)
            mod_obj = EraStdLibModule(name=alias, exports=exports)
            env.define(alias, mod_obj, is_mutable=False)
            return mod_obj

        elif isinstance(stmt, StructDecl):
            fields = stmt.fields
            methods = {}
            for m in stmt.methods:
                m_fn = EraFunction(
                    name=m.name,
                    params=m.params,
                    body=m.body,
                    closure=env,
                    capabilities=m.capabilities
                )
                methods[m.name] = m_fn

            struct_def = EraStructDef(name=stmt.name, fields=fields, methods=methods)

            def _struct_constructor(*args):
                field_values = {}
                for i, field in enumerate(fields):
                    if i < len(args):
                        field_values[field.name] = args[i]
                    elif field.default_value is not None:
                        field_values[field.name] = self.eval_expr(field.default_value, env)
                    else:
                        field_values[field.name] = EraOption.none()
                return EraStructInstance(struct_def=struct_def, fields=field_values)

            env.define(stmt.name, EraBuiltinFunction(stmt.name, _struct_constructor), is_mutable=False)
            return EraOption.none()

        elif isinstance(stmt, EnumDecl):
            enum_def = EraEnumDef(name=stmt.name, variants=stmt.variants)
            env.define(stmt.name, enum_def, is_mutable=False)
            return EraOption.none()

        elif isinstance(stmt, ActorDecl):
            # Actor definition
            def _actor_constructor(*args):
                actor_env = Environment(parent=env)
                # Initialize actor fields
                for f in stmt.fields:
                    self.eval_stmt(f, actor_env)
                # Define methods
                for m in stmt.methods:
                    self.eval_stmt(m, actor_env)
                return EraActor(name=stmt.name, env=actor_env)

            env.define(stmt.name, EraBuiltinFunction(stmt.name, _actor_constructor), is_mutable=False)
            return EraOption.none()

        elif isinstance(stmt, SpawnStmt):
            # Spawn green thread / fiber
            callee_fn = self.eval_expr(stmt.call.callee, env)
            arg_vals = [self.eval_expr(a, env) for a in stmt.call.arguments]

            def _thread_worker():
                self._invoke_function(callee_fn, arg_vals, stmt.location)

            t = threading.Thread(target=_thread_worker, daemon=True)
            t.start()
            return EraOption.none()

        elif isinstance(stmt, ExprStmt):
            return self.eval_expr(stmt.expression, env)

        return None

    # -------------------------------------------------------------------------
    # Expression Evaluation
    # -------------------------------------------------------------------------

    def eval_expr(self, expr: Expr, env: Environment) -> EraValue:
        if isinstance(expr, LiteralExpr):
            if expr.type_name == "int": return EraInt(expr.value)
            if expr.type_name == "float": return EraFloat(expr.value)
            if expr.type_name == "string": return EraString(expr.value)
            if expr.type_name == "bool": return EraBool(expr.value)

        elif isinstance(expr, IdentifierExpr):
            return env.get(expr.name)

        elif isinstance(expr, BinaryExpr):
            # Short-circuit logical ops
            if expr.operator.type == TokenType.AND:
                l = self.eval_expr(expr.left, env)
                if not l.is_truthy(): return l
                return self.eval_expr(expr.right, env)
            if expr.operator.type == TokenType.OR:
                l = self.eval_expr(expr.left, env)
                if l.is_truthy(): return l
                return self.eval_expr(expr.right, env)

            l = self.eval_expr(expr.left, env)
            r = self.eval_expr(expr.right, env)
            return self._eval_binary_op(l, expr.operator.type, r, expr.location)

        elif isinstance(expr, UnaryExpr):
            operand = self.eval_expr(expr.right, env)
            if expr.operator.type == TokenType.NOT:
                return EraBool(not operand.is_truthy())
            elif expr.operator.type == TokenType.MINUS:
                if isinstance(operand, EraInt): return EraInt(-operand.value)
                if isinstance(operand, EraFloat): return EraFloat(-operand.value)
                raise RuntimeError(f"Cannot apply unary '-' to '{operand.type_name()}'")

        elif isinstance(expr, CallExpr):
            callee = self.eval_expr(expr.callee, env)
            args = [self.eval_expr(a, env) for a in expr.arguments]
            return self._invoke_function(callee, args, expr.location)

        elif isinstance(expr, MemberExpr):
            target = self.eval_expr(expr.target, env)
            if isinstance(target, (PythonBridgeModule, EraStdLibModule)):
                return target.get_attr(expr.member)

            if isinstance(target, EraActor):
                with target.lock:
                    method = target.env.get(expr.member)
                    return method

            if isinstance(target, EraStructDef):
                if expr.member in target.methods:
                    return target.methods[expr.member]

            if isinstance(target, EraStructInstance):
                val = target.get(expr.member)
                if val is not None:
                    if isinstance(val, EraFunction):
                        def _bound_method(*args):
                            return self._invoke_function(val, [target, *args], expr.location)
                        return EraBuiltinFunction(f"{target.struct_def.name}.{expr.member}", _bound_method)
                    return val
                raise RuntimeError(f"Struct '{target.type_name()}' has no field or method '{expr.member}'")

            if isinstance(target, EraEnumDef):
                if expr.member in target.variants:
                    return target.get_variant(expr.member)
                raise RuntimeError(f"Enum '{target.name}' has no variant '{expr.member}'")

            if isinstance(target, EraEnumValue):
                if expr.member == "variant":
                    return EraString(target.variant)
                if expr.member == "inner":
                    return target.inner if target.inner else EraOption.none()

            if isinstance(target, EraArray):
                if expr.member == "push":
                    return EraBuiltinFunction("push", lambda val: (target.push(val), EraOption.none())[1])
                if expr.member == "pop":
                    return EraBuiltinFunction("pop", lambda: target.pop())
                if expr.member == "len":
                    return EraBuiltinFunction("len", lambda: EraInt(len(target.elements)))
                if expr.member == "map":
                    return EraBuiltinFunction("map", lambda fn: EraArray([self._invoke_function(fn, [e], expr.location) for e in target.elements]))
                if expr.member == "filter":
                    return EraBuiltinFunction("filter", lambda fn: EraArray([e for e in target.elements if self._invoke_function(fn, [e], expr.location).is_truthy()]))
                if expr.member == "reduce":
                    def _arr_reduce(fn, init_val):
                        acc = init_val
                        for e in target.elements:
                            acc = self._invoke_function(fn, [acc, e], expr.location)
                        return acc
                    return EraBuiltinFunction("reduce", _arr_reduce)
                if expr.member == "join":
                    return EraBuiltinFunction("join", lambda sep=EraString(","): EraString(sep.to_string().join(e.to_string() for e in target.elements)))
                if expr.member == "slice":
                    return EraBuiltinFunction("slice", lambda s, e=None: EraArray(target.elements[s.value : (e.value if (e and isinstance(e, EraInt)) else len(target.elements))]))
                if expr.member == "contains":
                    return EraBuiltinFunction("contains", lambda item: EraBool(any(e.to_string() == item.to_string() for e in target.elements)))
                if expr.member == "reverse":
                    return EraBuiltinFunction("reverse", lambda: EraArray(list(reversed(target.elements))))
                if expr.member == "sort":
                    return EraBuiltinFunction("sort", lambda: EraArray(sorted(target.elements, key=lambda x: x.value if hasattr(x, 'value') else str(x))))
                if expr.member == "find":
                    def _arr_find(fn):
                        for e in target.elements:
                            if self._invoke_function(fn, [e], expr.location).is_truthy():
                                return EraOption.some(e)
                        return EraOption.none()
                    return EraBuiltinFunction("find", _arr_find)

            if isinstance(target, EraString):
                if expr.member == "len":
                    return EraBuiltinFunction("len", lambda: EraInt(len(target.value)))
                if expr.member == "split":
                    return EraBuiltinFunction("split", lambda sep=EraString(" "): EraArray([EraString(s) for s in target.value.split(sep.to_string())]))
                if expr.member == "trim":
                    return EraBuiltinFunction("trim", lambda: EraString(target.value.strip()))
                if expr.member == "replace":
                    return EraBuiltinFunction("replace", lambda old_v, new_v: EraString(target.value.replace(old_v.to_string(), new_v.to_string())))
                if expr.member == "starts_with":
                    return EraBuiltinFunction("starts_with", lambda prefix: EraBool(target.value.startswith(prefix.to_string())))
                if expr.member == "ends_with":
                    return EraBuiltinFunction("ends_with", lambda suffix: EraBool(target.value.endswith(suffix.to_string())))
                if expr.member == "to_upper":
                    return EraBuiltinFunction("to_upper", lambda: EraString(target.value.upper()))
                if expr.member == "to_lower":
                    return EraBuiltinFunction("to_lower", lambda: EraString(target.value.lower()))
                if expr.member == "contains":
                    return EraBuiltinFunction("contains", lambda sub: EraBool(sub.to_string() in target.value))

            if isinstance(target, EraOption):
                if expr.member == "unwrap_or":
                    return EraBuiltinFunction("unwrap_or", lambda default_val: target.unwrap_or(default_val))
                if expr.member == "unwrap":
                    return EraBuiltinFunction("unwrap", lambda: target.val if target.is_some else self._raise_unwrap_error("Unwrapped None Option"))
                if expr.member == "is_some":
                    return EraBuiltinFunction("is_some", lambda: EraBool(target.is_some))
                if expr.member == "is_none":
                    return EraBuiltinFunction("is_none", lambda: EraBool(not target.is_some))
                if expr.member == "map":
                    return EraBuiltinFunction("map", lambda fn: EraOption.some(self._invoke_function(fn, [target.val], expr.location)) if target.is_some else EraOption.none())

            if isinstance(target, EraResult):
                if expr.member == "unwrap_or":
                    return EraBuiltinFunction("unwrap_or", lambda default_val: target.unwrap_or(default_val))
                if expr.member == "unwrap":
                    return EraBuiltinFunction("unwrap", lambda: target.val if target.is_ok else self._raise_unwrap_error(f"Unwrapped Err: {target.err.to_string()}"))
                if expr.member == "is_ok":
                    return EraBuiltinFunction("is_ok", lambda: EraBool(target.is_ok))
                if expr.member == "is_err":
                    return EraBuiltinFunction("is_err", lambda: EraBool(not target.is_ok))
                if expr.member == "map":
                    return EraBuiltinFunction("map", lambda fn: EraResult.ok(self._invoke_function(fn, [target.val], expr.location)) if target.is_ok else target)
                if expr.member == "map_err":
                    return EraBuiltinFunction("map_err", lambda fn: EraResult.err(self._invoke_function(fn, [target.err], expr.location)) if not target.is_ok else target)

            if isinstance(target, EraTensor):
                if expr.member == "shape":
                    return EraArray([EraInt(s) for s in target.shape])
                if expr.member == "sum":
                    return EraBuiltinFunction("sum", lambda: EraFloat(target.sum()))
                if expr.member == "mean":
                    return EraBuiltinFunction("mean", lambda: EraFloat(target.mean()))
                if expr.member == "transpose":
                    return EraBuiltinFunction("transpose", lambda: target.transpose())

            if isinstance(target, EraMap):
                if expr.member == "keys":
                    return EraBuiltinFunction("keys", lambda: EraArray([EraString(k) for k in target.entries.keys()]))
                if expr.member == "values":
                    return EraBuiltinFunction("values", lambda: EraArray(list(target.entries.values())))
                if expr.member == "len":
                    return EraBuiltinFunction("len", lambda: EraInt(len(target.entries)))
                if expr.member == "has_key":
                    return EraBuiltinFunction("has_key", lambda k: EraBool(k.to_string() in target.entries))

            if isinstance(target, EraChannel):
                if expr.member == "send":
                    return EraBuiltinFunction("send", lambda val: (target.send(val), EraOption.none())[1])
                if expr.member == "recv":
                    return EraBuiltinFunction("recv", lambda: target.recv())

            raise RuntimeError(f"Cannot access member '{expr.member}' on type '{target.type_name()}'")

        elif isinstance(expr, IndexExpr):
            target = self.eval_expr(expr.target, env)
            idx = self.eval_expr(expr.index, env)
            if isinstance(target, EraArray) and isinstance(idx, EraInt):
                return target.get(idx.value)
            if isinstance(target, EraMap) and isinstance(idx, EraString):
                return target.get(idx.value)
            if isinstance(target, EraString) and isinstance(idx, EraInt):
                if 0 <= idx.value < len(target.value):
                    return EraOption.some(EraString(target.value[idx.value]))
                return EraOption.none()
            raise RuntimeError(f"Cannot index '{target.type_name()}' with '{idx.type_name()}'")

        elif isinstance(expr, ArrayLitExpr):
            elems = [self.eval_expr(e, env) for e in expr.elements]
            return EraArray(elems)

        elif isinstance(expr, MapLitExpr):
            entries = {self.eval_expr(k, env).to_string(): self.eval_expr(v, env) for k, v in expr.entries}
            return EraMap(entries)

        elif isinstance(expr, OptionLitExpr):
            if expr.variant == "Some" and expr.value:
                return EraOption.some(self.eval_expr(expr.value, env))
            return EraOption.none()

        elif isinstance(expr, ResultLitExpr):
            if expr.variant == "Ok":
                return EraResult.ok(self.eval_expr(expr.value, env))
            return EraResult.err(self.eval_expr(expr.value, env))

        elif isinstance(expr, RangeExpr):
            start = self.eval_expr(expr.start, env)
            end = self.eval_expr(expr.end, env)
            if isinstance(start, EraInt) and isinstance(end, EraInt):
                s = start.value
                e = end.value if expr.half_open else end.value + 1
                return list(range(s, e))
            raise RuntimeError("Range bounds must be integers")

        elif isinstance(expr, MatchExpr):
            subject_val = self.eval_expr(expr.subject, env)
            for arm in expr.arms:
                matched, bindings = self._match_pattern(arm.pattern, subject_val)
                if matched:
                    arm_env = Environment(parent=env)
                    for k, v in bindings.items():
                        arm_env.define(k, v, is_mutable=False)
                    if arm.guard:
                        if not self.eval_expr(arm.guard, arm_env).is_truthy():
                            continue
                    if isinstance(arm.body, BlockExpr):
                        return self.eval_expr(arm.body, arm_env)
                    return self.eval_expr(arm.body, arm_env)

            raise RuntimeError(f"Unhandled pattern match for value: {subject_val.to_string()}")

        elif isinstance(expr, IfExpr):
            cond = self.eval_expr(expr.condition, env)
            if cond.is_truthy():
                return self.eval_expr(expr.then_branch, env)
            elif expr.else_branch:
                return self.eval_expr(expr.else_branch, env)
            return EraOption.none()

        elif isinstance(expr, BlockExpr):
            block_env = Environment(parent=env)
            res = EraOption.none()
            for s in expr.statements:
                res = self.eval_stmt(s, block_env)
            return res or EraOption.none()

        elif isinstance(expr, TensorLitExpr):
            args = [self.eval_expr(a, env) for a in expr.args]
            if expr.method == "zeros":
                shape = [x.value for x in args[0].elements] if isinstance(args[0], EraArray) else [2, 2]
                return EraTensor.zeros(shape)
            if expr.method == "ones":
                shape = [x.value for x in args[0].elements] if isinstance(args[0], EraArray) else [2, 2]
                return EraTensor.ones(shape)
            if expr.method == "randn":
                shape = [x.value for x in args[0].elements] if isinstance(args[0], EraArray) else [2, 2]
                return EraTensor.randn(shape)
            if expr.method == "from_array":
                if isinstance(args[0], EraArray):
                    return EraTensor.from_array(args[0])

        elif isinstance(expr, AICompleteExpr):
            p = self.eval_expr(expr.prompt, env).to_string()
            m = self.eval_expr(expr.model, env).to_string() if expr.model else "era-neural-v1"
            return AIRuntime.complete(prompt=p, model=m, schema=expr.schema_type)

        elif isinstance(expr, QuestionExpr):
            inner_val = self.eval_expr(expr.expr, env)
            if isinstance(inner_val, EraResult):
                if inner_val.is_ok:
                    return inner_val.val
                else:
                    # Early return error from caller
                    raise ReturnValue(inner_val)
            if isinstance(inner_val, EraOption):
                if inner_val.is_some:
                    return inner_val.val
                else:
                    raise ReturnValue(EraOption.none())
            return inner_val

        return EraOption.none()

    # -------------------------------------------------------------------------
    # Helper Execution Methods
    # -------------------------------------------------------------------------

    def _invoke_function(self, callee: EraValue, args: List[EraValue], loc: SourceLocation) -> EraValue:
        if isinstance(callee, EraEnumValue):
            inner = args[0] if args else None
            return EraEnumValue(enum_name=callee.enum_name, variant=callee.variant, inner=inner)

        if isinstance(callee, EraBuiltinFunction):
            return callee.func(*args)

        if isinstance(callee, EraFunction):
            fn_env = Environment(parent=callee.closure)

            # FRESH DEFAULT INSTANTIATION:
            # Re-evaluates default expression inside new invocation scope for each call
            for i, p in enumerate(callee.params):
                if i < len(args):
                    fn_env.define(p.name, args[i], is_mutable=True)
                elif p.default_value is not None:
                    fresh_val = self.eval_expr(p.default_value, fn_env)
                    fn_env.define(p.name, fresh_val, is_mutable=True)
                else:
                    raise RuntimeError(f"Missing required argument '{p.name}' in call to '{callee.name}'")

            try:
                self.eval_expr(callee.body, fn_env)
            except ReturnValue as ret:
                return ret.value
            return EraOption.none()

        raise RuntimeError(f"Cannot call non-function of type '{callee.type_name()}'")

    def _match_pattern(self, pattern: Pattern, val: EraValue) -> Tuple[bool, Dict[str, EraValue]]:
        if isinstance(pattern, WildcardPattern):
            return True, {}

        if isinstance(pattern, IdentifierPattern):
            return True, {pattern.name: val}

        if isinstance(pattern, LiteralPattern):
            if isinstance(val, (EraInt, EraFloat, EraString, EraBool)):
                return (val.value == pattern.value), {}
            return False, {}

        if isinstance(pattern, SomePattern):
            if isinstance(val, EraOption) and val.is_some:
                return self._match_pattern(pattern.inner, val.val)
            return False, {}

        if isinstance(pattern, NonePattern):
            return (isinstance(val, EraOption) and not val.is_some), {}

        if isinstance(pattern, OkPattern):
            if isinstance(val, EraResult) and val.is_ok:
                return self._match_pattern(pattern.inner, val.val)
            return False, {}

        if isinstance(pattern, ErrPattern):
            if isinstance(val, EraResult) and not val.is_ok:
                return self._match_pattern(pattern.inner, val.err)
            return False, {}

        if isinstance(pattern, EnumPattern):
            if isinstance(val, EraEnumValue) and val.enum_name == pattern.enum_name and val.variant == pattern.variant:
                if pattern.inner and val.inner:
                    return self._match_pattern(pattern.inner, val.inner)
                return True, {}
            return False, {}

        return False, {}

    def _raise_unwrap_error(self, msg: str):
        raise RuntimeError(f"Panic: {msg}")

    def _eval_binary_op(self, l: EraValue, op: TokenType, r: EraValue, loc: SourceLocation) -> EraValue:
        # Strict equality
        if op == TokenType.EQ:
            if isinstance(l, (EraInt, EraFloat)) and isinstance(r, (EraInt, EraFloat)):
                return EraBool(l.value == r.value)
            if isinstance(l, EraString) and isinstance(r, EraString):
                return EraBool(l.value == r.value)
            if isinstance(l, EraBool) and isinstance(r, EraBool):
                return EraBool(l.value == r.value)
            if isinstance(l, EraOption) and isinstance(r, EraOption):
                return EraBool(l.is_some == r.is_some and l.val == r.val)
            return EraBool(False)

        if op == TokenType.NEQ:
            eq_res = self._eval_binary_op(l, TokenType.EQ, r, loc)
            return EraBool(not eq_res.value)

        # Tensor Matrix Multiplication
        if op == TokenType.MATMUL:
            if isinstance(l, EraTensor) and isinstance(r, EraTensor):
                return l.matmul(r)
            raise RuntimeError(f"Operator '@' requires Tensors, got '{l.type_name()}' and '{r.type_name()}'")

        # Arithmetic operations
        if isinstance(l, EraInt) and isinstance(r, EraInt):
            if op == TokenType.PLUS: return EraInt(l.value + r.value)
            if op == TokenType.MINUS: return EraInt(l.value - r.value)
            if op == TokenType.STAR: return EraInt(l.value * r.value)
            if op == TokenType.SLASH:
                if r.value == 0: raise ZeroDivisionError("Division by zero in integer arithmetic")
                return EraInt(l.value // r.value)
            if op == TokenType.PERCENT: return EraInt(l.value % r.value)
            if op == TokenType.LT: return EraBool(l.value < r.value)
            if op == TokenType.LTE: return EraBool(l.value <= r.value)
            if op == TokenType.GT: return EraBool(l.value > r.value)
            if op == TokenType.GTE: return EraBool(l.value >= r.value)

        if isinstance(l, (EraInt, EraFloat)) and isinstance(r, (EraInt, EraFloat)):
            lv, rv = float(l.value), float(r.value)
            if op == TokenType.PLUS: return EraFloat(lv + rv)
            if op == TokenType.MINUS: return EraFloat(lv - rv)
            if op == TokenType.STAR: return EraFloat(lv * rv)
            if op == TokenType.SLASH:
                if rv == 0.0: raise ZeroDivisionError("Division by zero in float arithmetic")
                return EraFloat(lv / rv)
            if op == TokenType.LT: return EraBool(lv < rv)
            if op == TokenType.LTE: return EraBool(lv <= rv)
            if op == TokenType.GT: return EraBool(lv > rv)
            if op == TokenType.GTE: return EraBool(lv >= rv)

        # String concatenation (only explicit string + string)
        if isinstance(l, EraString) and isinstance(r, EraString):
            if op == TokenType.PLUS:
                return EraString(l.value + r.value)

        raise RuntimeError(f"Unsupported binary operation '{op.name}' between '{l.type_name()}' and '{r.type_name()}'")

    def _tensor_sum(self, tensor: EraTensor) -> EraFloat:
        def _flatten(d):
            if isinstance(d, (int, float)): yield d
            elif isinstance(d, list):
                for item in d: yield from _flatten(item)
        return EraFloat(sum(_flatten(tensor.data)))
