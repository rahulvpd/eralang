"""
EraLang Bytecode Compiler
Compiles AST into Bytecode Chunks with constants and instruction stream.
"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Any, Dict, Optional, Tuple
from .ast_nodes import (
    Program, Stmt, Expr, LetStmt, VarStmt, AssignStmt, FnDecl, ReturnStmt,
    ForStmt, WhileStmt, BreakStmt, ContinueStmt, ImportStmt, StructDecl, EnumDecl,
    ActorDecl, SpawnStmt, ExprStmt,
    LiteralExpr, IdentifierExpr, BinaryExpr, UnaryExpr,
    CallExpr, MemberExpr, IndexExpr, ArrayLitExpr, MapLitExpr,
    OptionLitExpr, ResultLitExpr, RangeExpr, MatchExpr, IfExpr, BlockExpr,
    TensorLitExpr, AICompleteExpr, QuestionExpr
)
from .token import TokenType
from .values import (
    EraValue, EraInt, EraFloat, EraString, EraBool, EraOption, EraResult, EraArray, EraFunction
)


class OpCode(Enum):
    OP_CONST = auto()
    OP_LOAD = auto()
    OP_STORE = auto()
    OP_POP = auto()
    OP_ADD = auto()
    OP_SUB = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_MATMUL = auto()
    OP_EQ = auto()
    OP_NEQ = auto()
    OP_LT = auto()
    OP_LTE = auto()
    OP_GT = auto()
    OP_GTE = auto()
    OP_NOT = auto()
    OP_NEG = auto()
    OP_JUMP = auto()
    OP_JUMP_IF_FALSE = auto()
    OP_CALL = auto()
    OP_RETURN = auto()
    OP_GET_MEMBER = auto()
    OP_SET_MEMBER = auto()
    OP_GET_INDEX = auto()
    OP_SET_INDEX = auto()
    OP_BUILD_ARRAY = auto()
    OP_BUILD_OPTION = auto()
    OP_BUILD_RESULT = auto()
    OP_EVAL_EXPR = auto()


@dataclass
class Instruction:
    op: OpCode
    arg: Any = None
    line: int = 0


class BytecodeChunk:
    def __init__(self, name: str = "<main>"):
        self.name = name
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []

    def add_constant(self, val: Any) -> int:
        for i, c in enumerate(self.constants):
            if type(c) == type(val) and hasattr(c, "value") and hasattr(val, "value") and c.value == val.value:
                return i
        self.constants.append(val)
        return len(self.constants) - 1

    def emit(self, op: OpCode, arg: Any = None, line: int = 0) -> int:
        self.instructions.append(Instruction(op=op, arg=arg, line=line))
        return len(self.instructions) - 1


class Compiler:
    def __init__(self):
        self.chunk = BytecodeChunk()

    def compile(self, program: Program) -> BytecodeChunk:
        for stmt in program.statements:
            self._compile_stmt(stmt)
        self.chunk.emit(OpCode.OP_RETURN, arg=None)
        return self.chunk

    def _compile_stmt(self, stmt: Stmt):
        if isinstance(stmt, (LetStmt, VarStmt)):
            self._compile_expr(stmt.initializer)
            self.chunk.emit(OpCode.OP_STORE, arg=stmt.name)

        elif isinstance(stmt, FnDecl):
            idx = self.chunk.add_constant(stmt)
            self.chunk.emit(OpCode.OP_CONST, arg=idx)
            self.chunk.emit(OpCode.OP_STORE, arg=stmt.name)

        elif isinstance(stmt, AssignStmt):
            self._compile_expr(stmt.value)
            if isinstance(stmt.target, IdentifierExpr):
                self.chunk.emit(OpCode.OP_STORE, arg=stmt.target.name)
            elif isinstance(stmt.target, MemberExpr):
                self._compile_expr(stmt.target.target)
                self.chunk.emit(OpCode.OP_SET_MEMBER, arg=stmt.target.member)

        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self._compile_expr(stmt.value)
            else:
                idx = self.chunk.add_constant(EraOption.none())
                self.chunk.emit(OpCode.OP_CONST, arg=idx)
            self.chunk.emit(OpCode.OP_RETURN)

        elif isinstance(stmt, ExprStmt):
            self._compile_expr(stmt.expression)
            self.chunk.emit(OpCode.OP_POP)

        elif isinstance(stmt, WhileStmt):
            # Pure VM while: condition jump + body + loop back
            loop_start = len(self.chunk.instructions)
            self._compile_expr(stmt.condition)
            jump_exit = self.chunk.emit(OpCode.OP_JUMP_IF_FALSE, arg=0)
            self._compile_expr(stmt.body)
            self.chunk.emit(OpCode.OP_POP)  # discard body result
            self.chunk.emit(OpCode.OP_JUMP, arg=loop_start)
            exit_pos = len(self.chunk.instructions)
            self.chunk.instructions[jump_exit].arg = exit_pos

        elif isinstance(stmt, (ForStmt, ImportStmt, StructDecl, EnumDecl, ActorDecl, SpawnStmt, BreakStmt, ContinueStmt)):
            # For loops and imports still delegated (For needs iterable handling, Import needs FS)
            # Emit as EVAL_EXPR - VM shares env via ev.global_env = self.env
            idx = self.chunk.add_constant(stmt)
            self.chunk.emit(OpCode.OP_EVAL_EXPR, arg=idx)
        elif isinstance(stmt, BlockExpr):
            for s in stmt.statements:
                self._compile_stmt(s)
        else:
            # General statement fallback - also delegate to evaluator
            idx = self.chunk.add_constant(stmt)
            self.chunk.emit(OpCode.OP_EVAL_EXPR, arg=idx)

    def _compile_expr(self, expr: Expr):
        if isinstance(expr, LiteralExpr):
            if expr.type_name == "int": val = EraInt(expr.value)
            elif expr.type_name == "float": val = EraFloat(expr.value)
            elif expr.type_name == "string": val = EraString(expr.value)
            elif expr.type_name == "bool": val = EraBool(expr.value)
            else: val = expr.value
            idx = self.chunk.add_constant(val)
            self.chunk.emit(OpCode.OP_CONST, arg=idx)

        elif isinstance(expr, IdentifierExpr):
            self.chunk.emit(OpCode.OP_LOAD, arg=expr.name)

        elif isinstance(expr, BinaryExpr):
            self._compile_expr(expr.left)
            self._compile_expr(expr.right)
            op_map = {
                TokenType.PLUS: OpCode.OP_ADD,
                TokenType.MINUS: OpCode.OP_SUB,
                TokenType.STAR: OpCode.OP_MUL,
                TokenType.SLASH: OpCode.OP_DIV,
                TokenType.MATMUL: OpCode.OP_MATMUL,
                TokenType.EQ: OpCode.OP_EQ,
                TokenType.NEQ: OpCode.OP_NEQ,
                TokenType.LT: OpCode.OP_LT,
                TokenType.LTE: OpCode.OP_LTE,
                TokenType.GT: OpCode.OP_GT,
                TokenType.GTE: OpCode.OP_GTE,
            }
            if expr.operator.type in op_map:
                self.chunk.emit(op_map[expr.operator.type])

        elif isinstance(expr, UnaryExpr):
            self._compile_expr(expr.right)
            if expr.operator.type == TokenType.NOT:
                self.chunk.emit(OpCode.OP_NOT)
            elif expr.operator.type == TokenType.MINUS:
                self.chunk.emit(OpCode.OP_NEG)

        elif isinstance(expr, MemberExpr):
            self._compile_expr(expr.target)
            self.chunk.emit(OpCode.OP_GET_MEMBER, arg=expr.member)

        elif isinstance(expr, IndexExpr):
            self._compile_expr(expr.target)
            self._compile_expr(expr.index)
            self.chunk.emit(OpCode.OP_GET_INDEX)

        elif isinstance(expr, CallExpr):
            for a in expr.arguments:
                self._compile_expr(a)
            self._compile_expr(expr.callee)
            self.chunk.emit(OpCode.OP_CALL, arg=len(expr.arguments))

        elif isinstance(expr, ArrayLitExpr):
            for e in expr.elements:
                self._compile_expr(e)
            self.chunk.emit(OpCode.OP_BUILD_ARRAY, arg=len(expr.elements))

        elif isinstance(expr, OptionLitExpr):
            if expr.variant == "Some" and expr.value:
                self._compile_expr(expr.value)
                self.chunk.emit(OpCode.OP_BUILD_OPTION, arg=True)
            else:
                self.chunk.emit(OpCode.OP_BUILD_OPTION, arg=False)

        elif isinstance(expr, ResultLitExpr):
            self._compile_expr(expr.value)
            self.chunk.emit(OpCode.OP_BUILD_RESULT, arg=(expr.variant == "Ok"))

        elif isinstance(expr, BlockExpr):
            for s in expr.statements:
                self._compile_stmt(s)

        elif isinstance(expr, RangeExpr):
            self._compile_expr(expr.start)
            self._compile_expr(expr.end)
            # Range is evaluated via EVAL_EXPR for correct list expansion
            idx = self.chunk.add_constant(expr)
            self.chunk.emit(OpCode.OP_EVAL_EXPR, arg=idx)

        elif isinstance(expr, IfExpr):
            # Pure VM: compile condition + jumps for then/else branches
            self._compile_expr(expr.condition)
            jump_else = self.chunk.emit(OpCode.OP_JUMP_IF_FALSE, arg=0)
            # Then branch
            self._compile_expr(expr.then_branch)
            jump_end = self.chunk.emit(OpCode.OP_JUMP, arg=0)
            # Else branch
            else_pos = len(self.chunk.instructions)
            self.chunk.instructions[jump_else].arg = else_pos
            if expr.else_branch:
                self._compile_expr(expr.else_branch)
            else:
                idx = self.chunk.add_constant(EraOption.none())
                self.chunk.emit(OpCode.OP_CONST, arg=idx)
            end_pos = len(self.chunk.instructions)
            self.chunk.instructions[jump_end].arg = end_pos

        elif isinstance(expr, MatchExpr):
            # Pure VM would need pattern jump table; delegate to evaluator for correctness
            idx = self.chunk.add_constant(expr)
            self.chunk.emit(OpCode.OP_EVAL_EXPR, arg=idx)

        elif isinstance(expr, (TensorLitExpr, AICompleteExpr, QuestionExpr, MapLitExpr)):
            idx = self.chunk.add_constant(expr)
            self.chunk.emit(OpCode.OP_EVAL_EXPR, arg=idx)

        else:
            idx = self.chunk.add_constant(expr)
            self.chunk.emit(OpCode.OP_EVAL_EXPR, arg=idx)
