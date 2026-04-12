from dataclasses import dataclass


@dataclass
class Token:
    offset_num: int
    intend: int


@dataclass
class PyLine:
    intend: int
    tokens: list[Token]
