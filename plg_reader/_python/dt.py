from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

SEPARATORS = frozenset("()[]{},:;.=+-*/%<>@\"'#\\")
MULTI_CHAR_OPS = frozenset(
    {
        "->",
        "==",
        "!=",
        "<=",
        ">=",
        "//",
        "**",
        "...",
        "<<",
        ">>",
        ":=",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "**=",
        "//=",
        "<<=",
        ">>=",
        "&=",
        "|=",
        "^=",
        "@=",
    }
)
KWORD = frozenset(
    {
        "and",
        "as",
        "assert",
        "await",
        "break",
        "case",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "False",
        "finally",
        "for",
        "from",
        "if",
        "import",
        "in",
        "is",
        "match",
        "None",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "True",
        "try",
        "while",
        "with",
    }
)
KWORD_BAN = frozenset({"async", "global", "lambda", "nonlocal", "yield"})


class TokenType(Enum):
    NAME = auto()
    KWORD = auto()
    OP = auto()
    NUMBER = auto()
    PARENTHESE_OPEN = auto()
    PARENTHESE_CLOSE = auto()
    COMMA = auto()
    DOT = auto()
    MULT_STRING = auto()
    STRING = auto()
    COMMENT = auto()


@dataclass
class Token:
    start: int
    data: Any
    type: TokenType
    subtype: str | None = None
    line_num: int = 0


@dataclass
class Line:
    indent: int
    line_num: int
    tokens: list[Token]


@dataclass
class MultilineState:
    prefix: str
    quote: str
    parts: list[str]
    start_col: int
    start_line: int
    tokens_before: list[Token] = field(default_factory=list)
