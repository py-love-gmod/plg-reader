from dataclasses import dataclass
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
    STRING = auto()  
    FORMATTED_STRING = auto()  
    COMMENT = auto()


@dataclass
class Token:
    pos: tuple[int, int]
    data: Any 
    type: TokenType


@dataclass
class Line:
    indent: int
    line_num: int
    tokens: list[Token]
