from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRAttribute, IRNode, IRSubscript
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

    index = parser.parse_expression()
    tok = parser.current()
    if tok is not None and tok.type == TokenType.OP and tok.data == ":":
        raise SyntaxError(
            f"Срезы не поддерживаются на строке {tok.pos[0]}, позиция {tok.pos[1]}"
        )

    parser.expect(TokenType.PARENTHESE_CLOSE, "]")
    return IRSubscript(pos=value.pos, value=value, index=index)
