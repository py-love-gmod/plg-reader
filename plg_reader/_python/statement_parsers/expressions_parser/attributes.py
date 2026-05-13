from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRAttribute, IRNode, IRSubscript
from .base import ExpressionParser


def parse_attribute(parser: ExpressionParser, value: IRNode) -> IRAttribute:
    parser.expect(TokenType.DOT)
    name_tok = parser.current()
    if name_tok is None or name_tok.type != TokenType.NAME:
        raise SyntaxError(
            f"Ожидалось имя атрибута, получено {name_tok.data if name_tok else 'EOF'}"
        )

    parser.advance()
    return IRAttribute(pos=value.pos, value=value, attr=name_tok.data)


def parse_subscript(parser: ExpressionParser, value: IRNode) -> IRSubscript:
    parser.expect(TokenType.PARENTHESE_OPEN, "[")
    index = parser.parse_expression()
    parser.expect(TokenType.PARENTHESE_CLOSE, "]")
    return IRSubscript(pos=value.pos, value=value, index=index)
