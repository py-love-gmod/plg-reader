from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import Iterator, Literal


@dataclass
class IRNode:
    pos: tuple[int, int]

    def walk(self) -> Iterator[IRNode]:
        """Рекурсивно обходит узел и все его дочерние IRNode."""
        yield self
        for fld in self.__dataclass_fields__:
            if fld == "pos":
                continue

            value = getattr(self, fld)
            if isinstance(value, IRNode):
                yield from value.walk()

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, IRNode):
                        yield from item.walk()

            elif isinstance(value, dict):
                for item in value.values():
                    if isinstance(item, IRNode):
                        yield from item.walk()

    def pretty(self, indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent
        lines.append(f"{prefix}{self.__class__.__name__}(")
        lines.append(f"{prefix}  pos=({self.pos[0]}, {self.pos[1]})")
        for fld in self.__dataclass_fields__:
            if fld == "pos":
                continue

            value = getattr(self, fld)
            if isinstance(value, list):
                if value:
                    lines.append(f"{prefix}  {fld}=[")
                    for item in value:
                        if isinstance(item, IRNode):
                            lines.append(item.pretty(indent + 2))

                        else:
                            lines.append(f"{prefix}    {item!r}")

                    lines.append(f"{prefix}  ]")

                else:
                    lines.append(f"{prefix}  {fld}=[]")

            elif isinstance(value, dict):
                if value:
                    lines.append(f"{prefix}  {fld}={{")
                    for k, v in value.items():
                        if isinstance(v, IRNode):
                            lines.append(f"{prefix}    {k}:")
                            lines.append(v.pretty(indent + 3))

                        else:
                            lines.append(f"{prefix}    {k}: {v!r}")

                    lines.append(f"{prefix}  }}")

                else:
                    lines.append(f"{prefix}  {fld}={{}}")

            elif isinstance(value, IRNode):
                lines.append(f"{prefix}  {fld}=")
                lines.append(value.pretty(indent + 2))

            else:
                if fld == "value" and hasattr(self, "prefix") and self.prefix:  # pyright: ignore[reportAttributeAccessIssue]
                    lines.append(f"{prefix}  {fld}={self.prefix}{value!r}")  # pyright: ignore[reportAttributeAccessIssue]

                else:
                    lines.append(f"{prefix}  {fld}={value!r}")

        lines.append(f"{prefix})")
        return "\n".join(lines)


@dataclass
class IRFile(IRNode):
    path: Path
    body: list[IRNode] = field(default_factory=list)
    imports: list[IRImport] = field(default_factory=list)

    def __post_init__(self):
        if not self.pos:
            self.pos = (1, 0)


@dataclass
class IRImport(IRNode):
    modules: list[str]
    names: list[str | tuple[str, str]]
    is_from: bool
    level: int = 0


# Выражения
@dataclass
class IRConstant(IRNode):
    value: object
    prefix: str = ""


@dataclass
class IRName(IRNode):
    name: str


@dataclass
class IRAttribute(IRNode):
    value: IRNode
    attr: str


@dataclass
class IRSubscript(IRNode):
    value: IRNode
    index: IRNode


@dataclass
class IRCall(IRNode):
    func: IRNode
    args: list[IRNode] = field(default_factory=list)
    kwargs: dict[str, IRNode] = field(default_factory=dict)


@dataclass
class IRUnaryOp(IRNode):
    op: str
    operand: IRNode


class IRBinOpType(IntEnum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    FLOORDIV = auto()
    MOD = auto()
    POW = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    IN = auto()
    NOT_IN = auto()
    IS = auto()
    IS_NOT = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()
    LSHIFT = auto()
    RSHIFT = auto()


@dataclass
class IRBinOp(IRNode):
    op: IRBinOpType
    left: IRNode
    right: IRNode


@dataclass
class IRIfExpr(IRNode):
    """Тернарный оператор: body if test else orelse"""

    test: IRNode
    body: IRNode
    orelse: IRNode


# Коллекции
@dataclass
class IRList(IRNode):
    elements: list[IRNode] = field(default_factory=list)


@dataclass
class IRTuple(IRNode):
    elements: list[IRNode] = field(default_factory=list)


@dataclass
class IRSet(IRNode):
    elements: list[IRNode] = field(default_factory=list)


@dataclass
class IRDictItem(IRNode):
    key: IRNode
    value: IRNode


@dataclass
class IRDict(IRNode):
    items: list[IRDictItem] = field(default_factory=list)


@dataclass
class IRFString(IRNode):
    prefix: str = ""
    parts: list[IRNode | str] = field(default_factory=list)


@dataclass
class IRFStringDebug(IRNode):
    expr: IRNode


# Операторы
@dataclass
class IRFunctionDef(IRNode):
    name: str
    params: list[IRParam] = field(default_factory=list)
    returns: IRNode | None = None
    body: list[IRNode] = field(default_factory=list)
    decorators: list[IRDecorator] = field(default_factory=list)


@dataclass
class IRParam(IRNode):
    name: str
    kind: Literal["positional", "star_arg", "kw_arg", "star", "slash"] = "positional"
    annotation: IRNode | None = None
    default: IRNode | None = None


@dataclass
class IRClassDef(IRNode):
    name: str
    bases: list[IRNode] = field(default_factory=list)
    body: list[IRNode] = field(default_factory=list)
    decorators: list[IRDecorator] = field(default_factory=list)


@dataclass
class IRDecorator(IRNode):
    expr: IRNode


@dataclass
class IRAssign(IRNode):
    targets: list[IRNode]
    value: IRNode
    is_aug: bool = False
    aug_op: IRBinOpType | None = None  # только для составного присваивания


@dataclass
class IRAnnotatedAssign(IRNode):
    target: IRNode
    annotation: IRNode | None = None
    value: IRNode | None = None


@dataclass
class IRExprStatement(IRNode):
    expr: IRNode


@dataclass
class IRIf(IRNode):
    test: IRNode
    body: list[IRNode] = field(default_factory=list)
    orelse: list[IRNode] = field(default_factory=list)


@dataclass
class IRWhile(IRNode):
    test: IRNode
    body: list[IRNode] = field(default_factory=list)


@dataclass
class IRFor(IRNode):
    target: IRNode
    iter: IRNode
    body: list[IRNode] = field(default_factory=list)


@dataclass
class IRReturn(IRNode):
    value: IRNode | None = None


@dataclass
class IRBreak(IRNode):
    pass


@dataclass
class IRContinue(IRNode):
    pass


@dataclass
class IRPass(IRNode):
    pass


@dataclass
class IRDelete(IRNode):
    targets: list[IRNode]


@dataclass
class IRRaise(IRNode):
    exc: IRNode | None = None
    cause: IRNode | None = None


@dataclass
class IRExceptHandler(IRNode):
    type: IRNode | None = None
    name: str | None = None
    body: list[IRNode] = field(default_factory=list)


@dataclass
class IRTry(IRNode):
    body: list[IRNode] = field(default_factory=list)
    handlers: list[IRExceptHandler] = field(default_factory=list)
    orelse: list[IRNode] = field(default_factory=list)
    finalbody: list[IRNode] = field(default_factory=list)


@dataclass
class IRWithItem(IRNode):
    context_expr: IRNode
    optional_vars: IRNode | None = None


@dataclass
class IRWith(IRNode):
    items: list[IRWithItem] = field(default_factory=list)
    body: list[IRNode] = field(default_factory=list)


@dataclass
class IRComment(IRNode):
    text: str
