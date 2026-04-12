from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any

KWORD_SET = frozenset(
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

KWORD_SET_BAN = frozenset(
    {
        "async",  # forbitten
        "global",  # forbitten
        "lambda",  # forbitten
        "nonlocal",  # forbitten
        "yield",  # forbitten
    }
)


class TokenType(IntEnum):
    NAME = auto()
    KWORD = auto()
    OP = auto()

    NUMBER = auto()

    M_STRING = auto()
    STRING = auto()

    NL = auto()

    DOT = auto()
    ARROW = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()


@dataclass
class Token:
    line_num: int
    offset_num: int

    type_enum: TokenType
    value: Any
    subtype: Any


@dataclass
class PyLine:
    intend: int
    tokens: list[Token]
