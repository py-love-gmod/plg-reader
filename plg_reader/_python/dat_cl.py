from __future__ import annotations

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
STRING_PREFIXES = frozenset({"f", "r", "fr", "rf", "b", "u", "br", "rb"})
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


@dataclass
class RawLine:
    indent: int
    abs_indent: int
    raw_strs: list[str]
    line_num: int
    is_string_content: bool = False


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
    subtype: str | None


@dataclass
class Line:
    indent: int
    line_num: int
    tokens: list[Token]
