"""
EraLang Token Specification and Source Tracking
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    # End of File & Special
    EOF = auto()
    ERROR = auto()
    NEWLINE = auto()

    # Literals
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()
    BOOLEAN = auto()

    # Keywords
    LET = auto()          # let (immutable)
    VAR = auto()          # var (mutable)
    FN = auto()           # fn
    RETURN = auto()       # return
    IF = auto()           # if
    ELSE = auto()         # else
    MATCH = auto()        # match
    FOR = auto()          # for
    IN = auto()           # in
    WHILE = auto()        # while
    BREAK = auto()        # break
    CONTINUE = auto()     # continue
    IMPORT = auto()       # import
    AS = auto()           # as
    ACTOR = auto()        # actor
    SPAWN = auto()        # spawn
    TYPE = auto()         # type
    STRUCT = auto()       # struct
    ENUM = auto()         # enum
    WITH = auto()         # with (capabilities)

    # First-class Safety & AI keywords/constructs
    SOME = auto()         # Some
    NONE = auto()         # None
    OK = auto()           # Ok
    ERR = auto()          # Err
    TENSOR = auto()       # Tensor
    CHAN = auto()         # Chan
    AI = auto()           # ai

    # Operators
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    PERCENT = auto()      # %
    MATMUL = auto()       # @ (Tensor matrix multiplication)
    
    ASSIGN = auto()       # =
    PLUS_ASSIGN = auto()  # +=
    MINUS_ASSIGN = auto() # -=
    STAR_ASSIGN = auto()  # *=
    SLASH_ASSIGN = auto() # /=

    EQ = auto()           # ==
    NEQ = auto()          # !=
    LT = auto()           # <
    LTE = auto()          # <=
    GT = auto()           # >
    GTE = auto()          # >=

    AND = auto()          # &&
    OR = auto()           # ||
    NOT = auto()          # !

    ARROW = auto()        # -> (function return type)
    FAT_ARROW = auto()    # => (match arm)
    DOT_DOT_LT = auto()   # ..< (half-open range 0..<n)
    DOT_DOT = auto()      # .. (closed range)
    DOT = auto()          # .
    COMMA = auto()        # ,
    COLON = auto()        # :
    SEMICOLON = auto()    # ;
    QUESTION = auto()     # ? (safe unwrap / error propagation)

    # Delimiters
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]


KEYWORDS = {
    "let": TokenType.LET,
    "var": TokenType.VAR,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "match": TokenType.MATCH,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "while": TokenType.WHILE,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "import": TokenType.IMPORT,
    "as": TokenType.AS,
    "actor": TokenType.ACTOR,
    "spawn": TokenType.SPAWN,
    "type": TokenType.TYPE,
    "struct": TokenType.STRUCT,
    "enum": TokenType.ENUM,
    "with": TokenType.WITH,
    "Some": TokenType.SOME,
    "None": TokenType.NONE,
    "Ok": TokenType.OK,
    "Err": TokenType.ERR,
    "Tensor": TokenType.TENSOR,
    "Chan": TokenType.CHAN,
    "ai": TokenType.AI,
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
}


@dataclass
class SourceLocation:
    line: int
    column: int
    filename: str = "<stdin>"

    def __str__(self) -> str:
        return f"{self.filename}:{self.line}:{self.column}"


@dataclass
class Token:
    type: TokenType
    lexeme: str
    value: Any
    location: SourceLocation

    def __str__(self) -> str:
        return f"Token({self.type.name}, '{self.lexeme}', val={self.value}, loc={self.location})"
