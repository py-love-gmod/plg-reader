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
    pos: tuple[int, int]
    data: Any
    type: TokenType
    subtype: str | None = None


@dataclass
class Line:
    indent: int
    line_num: int
    tokens: list[Token]


@dataclass
class MultilineState:  # ???
    prefix: str
    quote: str
    parts: list[str]
    start_pos: tuple[int, int]
    tokens_before: list[Token] = field(default_factory=list)


# TODO: По большому счёту текущая система мультилайн стейта
# не работает от слова совсем для f-strings.

# Для того чтобы это хотя-бы в теории было нормально обрабатывать необходимо
# эту дичь не как мультилайн стринг(?),
# а скорее как мультистейт строку. (возможно лайн в лайне? Условно конечно)

# Я думаю самое разумное ввести специальную структуру контейнер, которая будет обрабатываться иначе. Условно PyString(?).
# Название не очень удачное правда. По хорошему должен быть контейнер в котором будет или тип токена STRING, или же другой оператор.
# КРАЙНЕ необходимо сделать отдельный контейнер, в противном случае на моменте билда IR я схаваю говна из-за невозможности определить
# где находится специализированная граматика f строк. Для примера строка f"Sential {obj=}" при разбивании на обычные токены без контейнера
# вызовут проблему парсинга из-за отсутствия правого операнда для бинарного оператора.

# Само же по себе это скорее всего должно разбиваться во что-то такое:
# Исходная строка: f"Sential {obj=}"
# Выходная структура: Условный_Контейнер_Для_Строк(
#   prefixis="f",
#   data=[Token(type=string, data="Sential "), Token(type=name, data="obj"), Token(type=op, data="=")]
# )
# Но это моё примерное предположение структуры. Как оно будет в уже проде не особо понятно. 
# Я только смутно представляю более верный уровень на текущий момент

# Так же Token.subtype выглядит как юзлес поле во всём проекте.
# Оно используется для мультичар операторов (когда есть поле data просто которое и должно жрать и обрабатывать всё это говно)
# Изначально subtype был сделан для строковых литералов,
# но я не вижу смысла если "Условный_Контейнер_Для_Строк" будет держать эту информацию subtype станет легаси.
