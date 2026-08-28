"""
EraLang Abstract Syntax Tree (AST) Node Definitions
"""
from dataclasses import dataclass
from typing import List, Optional, Any, Tuple
from .token import Token, SourceLocation


class ASTNode:
    location: SourceLocation


# ==============================================================================
# Patterns for Pattern Matching (match expressions)
# ==============================================================================

class Pattern(ASTNode):
    pass


@dataclass
class WildcardPattern(Pattern):
    location: SourceLocation


@dataclass
class LiteralPattern(Pattern):
    value: Any
    location: SourceLocation


@dataclass
class IdentifierPattern(Pattern):
    name: str
    location: SourceLocation


@dataclass
class SomePattern(Pattern):
    inner: Pattern
    location: SourceLocation


@dataclass
class NonePattern(Pattern):
    location: SourceLocation


@dataclass
class OkPattern(Pattern):
    inner: Pattern
    location: SourceLocation


@dataclass
class ErrPattern(Pattern):
    inner: Pattern
    location: SourceLocation


@dataclass
class EnumPattern(Pattern):
    enum_name: str
    variant: str
    inner: Optional[Pattern] = None
    location: SourceLocation = None


@dataclass
class MatchArm(ASTNode):
    pattern: Pattern
    guard: Optional['Expr']
    body: ASTNode
    location: SourceLocation


# ==============================================================================
# Expressions
# ==============================================================================

class Expr(ASTNode):
    pass


@dataclass
class LiteralExpr(Expr):
    value: Any
    type_name: str
    location: SourceLocation


@dataclass
class IdentifierExpr(Expr):
    name: str
    location: SourceLocation


@dataclass
class BinaryExpr(Expr):
    left: Expr
    operator: Token
    right: Expr
    location: SourceLocation


@dataclass
class UnaryExpr(Expr):
    operator: Token
    right: Expr
    location: SourceLocation


@dataclass
class CallExpr(Expr):
    callee: Expr
    arguments: List[Expr]
    location: SourceLocation


@dataclass
class MemberExpr(Expr):
    target: Expr
    member: str
    location: SourceLocation


@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr
    location: SourceLocation


@dataclass
class ArrayLitExpr(Expr):
    elements: List[Expr]
    location: SourceLocation


@dataclass
class MapLitExpr(Expr):
    entries: List[Tuple[Expr, Expr]]
    location: SourceLocation


@dataclass
class OptionLitExpr(Expr):
    variant: str  # "Some" | "None"
    value: Optional[Expr]
    location: SourceLocation


@dataclass
class ResultLitExpr(Expr):
    variant: str  # "Ok" | "Err"
    value: Expr
    location: SourceLocation


@dataclass
class RangeExpr(Expr):
    start: Expr
    end: Expr
    half_open: bool  # True for 0..<n, False for 0..n
    location: SourceLocation


@dataclass
class MatchExpr(Expr):
    subject: Expr
    arms: List[MatchArm]
    location: SourceLocation


@dataclass
class IfExpr(Expr):
    condition: Expr
    then_branch: ASTNode
    else_branch: Optional[ASTNode]
    location: SourceLocation


@dataclass
class BlockExpr(Expr):
    statements: List['Stmt']
    location: SourceLocation


@dataclass
class TensorLitExpr(Expr):
    method: str       # "zeros", "ones", "randn", "from_array"
    args: List[Expr]
    location: SourceLocation


@dataclass
class AICompleteExpr(Expr):
    prompt: Expr
    model: Optional[Expr]
    schema_type: Optional[str]
    location: SourceLocation


@dataclass
class QuestionExpr(Expr):
    expr: Expr
    location: SourceLocation


# ==============================================================================
# Statements
# ==============================================================================

class Stmt(ASTNode):
    pass


@dataclass
class Param(ASTNode):
    name: str
    type_annotation: Optional[str]
    default_value: Optional[Expr]
    location: SourceLocation


@dataclass
class LetStmt(Stmt):
    name: str
    type_annotation: Optional[str]
    initializer: Expr
    location: SourceLocation


@dataclass
class VarStmt(Stmt):
    name: str
    type_annotation: Optional[str]
    initializer: Expr
    location: SourceLocation


@dataclass
class AssignStmt(Stmt):
    target: Expr
    op: Token
    value: Expr
    location: SourceLocation


@dataclass
class FnDecl(Stmt):
    name: str
    params: List[Param]
    return_type: Optional[str]
    body: BlockExpr
    capabilities: List[str]
    location: SourceLocation


@dataclass
class ReturnStmt(Stmt):
    value: Optional[Expr]
    location: SourceLocation


@dataclass
class ForStmt(Stmt):
    var_name: str
    iterable: Expr
    body: BlockExpr
    location: SourceLocation


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: BlockExpr
    location: SourceLocation


@dataclass
class BreakStmt(Stmt):
    location: SourceLocation


@dataclass
class ContinueStmt(Stmt):
    location: SourceLocation


@dataclass
class ImportStmt(Stmt):
    kind: str       # "era", "python", "c", "js", "rust"
    module_path: str
    alias: Optional[str]
    location: SourceLocation


@dataclass
class ActorDecl(Stmt):
    name: str
    fields: List[Stmt]
    methods: List[FnDecl]
    location: SourceLocation


@dataclass
class StructField(ASTNode):
    name: str
    type_annotation: Optional[str]
    default_value: Optional[Expr]
    location: SourceLocation


@dataclass
class StructDecl(Stmt):
    name: str
    fields: List[StructField]
    methods: List[FnDecl]
    location: SourceLocation


@dataclass
class EnumDecl(Stmt):
    name: str
    variants: List[str]
    location: SourceLocation


@dataclass
class SpawnStmt(Stmt):
    call: CallExpr
    location: SourceLocation


@dataclass
class ExprStmt(Stmt):
    expression: Expr
    location: SourceLocation


@dataclass
class Program(ASTNode):
    statements: List[Stmt]
    location: SourceLocation
