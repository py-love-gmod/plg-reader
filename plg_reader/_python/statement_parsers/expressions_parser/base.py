from __future__ import annotations

from ...file_parse_dt import Token, TokenType
from ...ir_builder_dt import IRBinOp, IRBinOpType, IRNode, IRUnaryOp

BINARY_PREC = {
    "or": 1,
    "and": 2,
    "==": 4,
    "!=": 4,
    "<": 4,
    ">": 4,
    "<=": 4,
    ">=": 4,
    "in": 4,
    "not in": 4,
    "is": 4,
    "is not": 4,
    "|": 5,
    "^": 6,
    "&": 7,
    "<<": 8,
    ">>": 8,
    "+": 9,
    "-": 9,
    "*": 10,
    "/": 10,
    "//": 10,
    "%": 10,
    "**": 11,
}
BINARY_OPS = frozenset(BINARY_PREC)
UNARY_PREC = 12


def op_to_enum(op: str) -> IRBinOpType:
    mapping = {
        "+": IRBinOpType.ADD,
        "-": IRBinOpType.SUB,
        "*": IRBinOpType.MUL,
        "/": IRBinOpType.DIV,
        "//": IRBinOpType.FLOORDIV,
        "%": IRBinOpType.MOD,
        "**": IRBinOpType.POW,
        "==": IRBinOpType.EQ,
        "!=": IRBinOpType.NE,
        "<": IRBinOpType.LT,
        ">": IRBinOpType.GT,
        "<=": IRBinOpType.LE,
        ">=": IRBinOpType.GE,
        "and": IRBinOpType.AND,
        "or": IRBinOpType.OR,
        "in": IRBinOpType.IN,
        "not in": IRBinOpType.NOT_IN,
        "is": IRBinOpType.IS,
        "is not": IRBinOpType.IS_NOT,
        "|": IRBinOpType.BIT_OR,
        "^": IRBinOpType.BIT_XOR,
        "&": IRBinOpType.BIT_AND,
        "<<": IRBinOpType.LSHIFT,
        ">>": IRBinOpType.RSHIFT,
    }
    return mapping[op]


class ExpressionParser:
    def __init__(self, tokens: list[Token], start: int = 0):
        self.tokens = tokens
        self.pos = start

    def current(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> Token | None:
        tok = self.current()
        if tok:
            self.pos += 1

        return tok

    def expect(self, type_: TokenType, value: str | None = None) -> Token:
        tok = self.current()
        if tok is None:
            raise SyntaxError(
                f"Неожиданный конец выражения, ожидалось {value or type_}"
            )

        if tok.type != type_ or (value is not None and tok.data != value):
            raise SyntaxError(
                f"Ожидалось {value or type_}, получено {tok.data} "
                f"на строке {tok.pos[0]}, позиция {tok.pos[1]}"
            )

        self.advance()
        return tok

    def parse(self) -> IRNode:
        node = self.parse_expression()
        cur = self.current()
        if cur is not None:
            raise SyntaxError(f"Неожиданный токен {cur.data} в конце выражения")

        return node

    def parse_expression(self, min_prec: int = 0) -> IRNode:
        tok = self.current()
        if tok is None:
            raise SyntaxError("Пустое выражение")

        left = self.parse_prefix()
        while True:
            tok = self.current()
            if tok is None or tok.type != TokenType.OP or tok.data not in BINARY_OPS:
                break

            prec = BINARY_PREC[tok.data]
            if prec < min_prec:
                break

            op = self.advance()
            assert op is not None
            right = self.parse_expression(prec + 1)
            left = IRBinOp(pos=left.pos, op=op_to_enum(op.data), left=left, right=right)

        return left

    def parse_prefix(self) -> IRNode:
        tok = self.current()
        if tok is None:
            raise SyntaxError("Пустое выражение")

        if tok.type == TokenType.OP and tok.data in ("+", "-", "not", "~"):
            op = tok.data
            self.advance()
            operand = self.parse_expression(UNARY_PREC)
            return IRUnaryOp(pos=tok.pos, op=op, operand=operand)

        node = self.parse_atom()
        return self.parse_postfix_chain(node)

    def parse_atom(self) -> IRNode:
        raise NotImplementedError("parse_atom должен быть переопределён")

    def parse_postfix_chain(self, node: IRNode) -> IRNode:
        raise NotImplementedError("parse_postfix_chain должен быть переопределён")
