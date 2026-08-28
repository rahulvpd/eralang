"""
EraLang Stack-Based Virtual Machine (VM)
High-performance bytecode executor with constant pool and operand stack.
"""
from typing import List, Any, Dict, Optional, Tuple
from .compiler import BytecodeChunk, Instruction, OpCode
from .values import (
    EraValue, EraInt, EraFloat, EraString, EraBool, EraOption, EraResult, EraArray,
    EraBuiltinFunction, EraFunction, EraTensor
)
from .ast_nodes import FnDecl, Stmt, Expr
from .environment import Environment


class VM:
    def __init__(self, chunk: BytecodeChunk, env: Optional[Environment] = None):
        self.chunk = chunk
        self.env = env or Environment()
        self.stack: List[EraValue] = []
        self.ip = 0
        self._init_builtins()

    def _init_builtins(self):
        def _print(*args):
            print(" ".join(a.to_string() for a in args))
            return EraOption.none()

        if not self.env.exists("print"):
            self.env.define("print", EraBuiltinFunction("print", _print), is_mutable=False)
            self.env.define("to_str", EraBuiltinFunction("to_str", lambda x: EraString(x.to_string())), is_mutable=False)

    def run(self) -> EraValue:
        while self.ip < len(self.chunk.instructions):
            inst = self.chunk.instructions[self.ip]
            self.ip += 1
            op = inst.op

            if op == OpCode.OP_CONST:
                val = self.chunk.constants[inst.arg]
                if isinstance(val, FnDecl):
                    fn_obj = EraFunction(
                        name=val.name,
                        params=val.params,
                        body=val.body,
                        closure=self.env
                    )
                    self.stack.append(fn_obj)
                else:
                    self.stack.append(val)

            elif op == OpCode.OP_LOAD:
                val = self.env.get(inst.arg)
                self.stack.append(val)

            elif op == OpCode.OP_STORE:
                val = self.stack.pop()
                if self.env.exists(inst.arg):
                    self.env.assign(inst.arg, val)
                else:
                    self.env.define(inst.arg, val, is_mutable=True)

            elif op == OpCode.OP_POP:
                if self.stack:
                    self.stack.pop()

            elif op == OpCode.OP_ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, EraInt) and isinstance(b, EraInt):
                    self.stack.append(EraInt(a.value + b.value))
                elif isinstance(a, (EraInt, EraFloat)) and isinstance(b, (EraInt, EraFloat)):
                    self.stack.append(EraFloat(float(a.value) + float(b.value)))
                elif isinstance(a, EraString) and isinstance(b, EraString):
                    self.stack.append(EraString(a.value + b.value))
                elif isinstance(a, EraString):
                    self.stack.append(EraString(a.value + b.to_string()))
                elif isinstance(b, EraString):
                    self.stack.append(EraString(a.to_string() + b.value))
                else:
                    raise RuntimeError(f"Cannot add {a.type_name()} and {b.type_name()}")

            elif op == OpCode.OP_SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, EraInt) and isinstance(b, EraInt):
                    self.stack.append(EraInt(a.value - b.value))
                elif isinstance(a, (EraInt, EraFloat)) and isinstance(b, (EraInt, EraFloat)):
                    self.stack.append(EraFloat(float(a.value) - float(b.value)))

            elif op == OpCode.OP_MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, EraInt) and isinstance(b, EraInt):
                    self.stack.append(EraInt(a.value * b.value))
                elif isinstance(a, (EraInt, EraFloat)) and isinstance(b, (EraInt, EraFloat)):
                    self.stack.append(EraFloat(float(a.value) * float(b.value)))

            elif op == OpCode.OP_DIV:
                b = self.stack.pop()
                a = self.stack.pop()
                if b.value == 0:
                    raise ZeroDivisionError("Division by zero in VM")
                if isinstance(a, EraInt) and isinstance(b, EraInt):
                    self.stack.append(EraInt(a.value // b.value))
                else:
                    self.stack.append(EraFloat(float(a.value) / float(b.value)))

            elif op == OpCode.OP_MATMUL:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, EraTensor) and isinstance(b, EraTensor):
                    self.stack.append(a.matmul(b))
                else:
                    raise RuntimeError("Matmul requires Tensors")

            elif op == OpCode.OP_EQ:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(EraBool(a.to_string() == b.to_string()))

            elif op == OpCode.OP_NEQ:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(EraBool(a.to_string() != b.to_string()))

            elif op == OpCode.OP_LT:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(EraBool(a.value < b.value))

            elif op == OpCode.OP_LTE:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(EraBool(a.value <= b.value))

            elif op == OpCode.OP_GT:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(EraBool(a.value > b.value))

            elif op == OpCode.OP_GTE:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(EraBool(a.value >= b.value))

            elif op == OpCode.OP_NOT:
                a = self.stack.pop()
                self.stack.append(EraBool(not a.is_truthy()))

            elif op == OpCode.OP_NEG:
                a = self.stack.pop()
                if isinstance(a, EraInt):
                    self.stack.append(EraInt(-a.value))
                elif isinstance(a, EraFloat):
                    self.stack.append(EraFloat(-a.value))

            elif op == OpCode.OP_CALL:
                callee = self.stack.pop()
                arg_count = inst.arg
                args = [self.stack.pop() for _ in range(arg_count)]
                args.reverse()
                if isinstance(callee, EraBuiltinFunction):
                    res = callee.func(*args)
                    self.stack.append(res if res is not None else EraOption.none())
                elif isinstance(callee, EraFunction):
                    from .evaluator import Evaluator
                    ev = Evaluator()
                    res = ev._invoke_function(callee, args, None)
                    self.stack.append(res if res is not None else EraOption.none())

            elif op == OpCode.OP_GET_MEMBER:
                target = self.stack.pop()
                if isinstance(target, EraArray) and inst.arg == "len":
                    self.stack.append(EraBuiltinFunction("len", lambda: EraInt(len(target.elements))))
                elif isinstance(target, EraOption) and inst.arg == "unwrap_or":
                    self.stack.append(EraBuiltinFunction("unwrap_or", lambda d: target.unwrap_or(d)))
                elif isinstance(target, EraResult) and inst.arg == "unwrap_or":
                    self.stack.append(EraBuiltinFunction("unwrap_or", lambda d: target.unwrap_or(d)))

            elif op == OpCode.OP_BUILD_ARRAY:
                count = inst.arg
                items = [self.stack.pop() for _ in range(count)]
                items.reverse()
                self.stack.append(EraArray(items))

            elif op == OpCode.OP_BUILD_OPTION:
                is_some = inst.arg
                if is_some:
                    v = self.stack.pop()
                    self.stack.append(EraOption.some(v))
                else:
                    self.stack.append(EraOption.none())

            elif op == OpCode.OP_BUILD_RESULT:
                is_ok = inst.arg
                v = self.stack.pop()
                if is_ok:
                    self.stack.append(EraResult.ok(v))
                else:
                    self.stack.append(EraResult.err(v))

            elif op == OpCode.OP_JUMP:
                self.ip = inst.arg

            elif op == OpCode.OP_JUMP_IF_FALSE:
                cond = self.stack.pop()
                if not cond.is_truthy():
                    self.ip = inst.arg

            elif op == OpCode.OP_EVAL_EXPR:
                ast_node = self.chunk.constants[inst.arg]
                from .evaluator import Evaluator
                ev = Evaluator()
                # Share env so loops/structs see same scope
                ev.global_env = self.env
                if isinstance(ast_node, Stmt):
                    res = ev.eval_stmt(ast_node, self.env)
                    if res is not None and not isinstance(res, EraOption):
                        self.stack.append(res)
                elif isinstance(ast_node, Expr):
                    res = ev.eval_expr(ast_node, self.env)
                    if res is not None:
                        self.stack.append(res)

            elif op == OpCode.OP_RETURN:
                return self.stack.pop() if self.stack else EraOption.none()

        return self.stack.pop() if self.stack else EraOption.none()
