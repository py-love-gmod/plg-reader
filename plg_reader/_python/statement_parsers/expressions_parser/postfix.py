from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRNode
from .attributes import parse_attribute, parse_subscript
from .base import ExpressionParser
from .calls import parse_call


def parse_postfix_chain(parser: ExpressionParser, node: IRNode) -> IRNode:
    while True:
        tok = parser.current()
        if tok is None:
            break

        if tok.type == TokenType.PARENTHESE_OPEN and tok.data == "(":
            node = parse_call(parser, node)

        elif tok.type == TokenType.DOT:
            node = parse_attribute(parser, node)

        elif tok.type == TokenType.PARENTHESE_OPEN and tok.data == "[":
            node = parse_subscript(parser, node)

        else:
            break

    return node
