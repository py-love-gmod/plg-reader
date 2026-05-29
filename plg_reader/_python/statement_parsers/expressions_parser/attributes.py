from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRAttribute, IRNode, IRSubscript, IRTuple
from .base import ExpressionParser
from .utils import require_not_none


def parse_attribute(parser: ExpressionParser, value: IRNode) -> IRAttribute:
    parser.expect(TokenType.DOT)
    name_tok = require_not_none(parser.current(), "атрибута")
    if name_tok.type != TokenType.NAME:
        raise SyntaxError(
            f"Ожидалось имя атрибута, получено {name_tok.data if name_tok else 'EOF'}"
        )

    parser.advance()
    return IRAttribute(pos=value.pos, value=value, attr=name_tok.data)


def parse_subscript(parser: ExpressionParser, value: IRNode) -> IRSubscript:
    parser.expect(TokenType.PARENTHESE_OPEN, "[")

    tok = parser.current()
    if tok is not None and tok.type == TokenType.OP and tok.data == ":":
        raise SyntaxError(
            f"Срезы не поддерживаются на строке {tok.pos[0]}, позиция {tok.pos[1]}"
        )

    indexes = [parser.parse_expression()]
    tok = parser.current()
    while tok is not None and tok.type == TokenType.COMMA:
        parser.advance()
        tok = parser.current()
        if tok is not None and tok.type != TokenType.PARENTHESE_CLOSE:
            indexes.append(parser.parse_expression())

        else:
            break

        tok = parser.current()

    parser.expect(TokenType.PARENTHESE_CLOSE, "]")
    index = (
        indexes[0]
        if len(indexes) == 1
        else IRTuple(pos=indexes[0].pos, elements=indexes)
    )
    return IRSubscript(pos=value.pos, value=value, index=index)
