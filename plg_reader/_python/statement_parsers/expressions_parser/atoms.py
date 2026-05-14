from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRConstant, IRFString, IRName, IRNode, IRTuple
from .base import ExpressionParser
from .collections import parse_brace_collection, parse_list, parse_tuple
from .utils import require_not_none


def parse_atom(parser: ExpressionParser) -> IRNode:
    tok = require_not_none(parser.current())

    if tok.type == TokenType.NUMBER:
        parser.advance()
        return IRConstant(pos=tok.pos, value=tok.data)

    if tok.type == TokenType.NAME:
        parser.advance()
        return IRName(pos=tok.pos, name=tok.data)

    if tok.type == TokenType.STRING:
        parser.advance()
        _, s = tok.data
        return IRConstant(pos=tok.pos, value=s)

    if tok.type == TokenType.FORMATTED_STRING:
        return parse_fstring(parser)

    if tok.type == TokenType.PARENTHESE_OPEN:
        if tok.data == "(":
            return parse_paren(parser)

        elif tok.data == "[":
            parser.advance()
            return parse_list(parser, tok.pos)

        elif tok.data == "{":
            parser.advance()
            return parse_brace_collection(parser, tok.pos)

    if tok.type == TokenType.PARENTHESE_CLOSE:
        raise SyntaxError(
            f"Неожиданная закрывающая скобка на строке {tok.pos[0]}, позиция {tok.pos[1]}"
        )

    raise SyntaxError(
        f"Неожиданный токен {tok.data} на строке {tok.pos[0]}, позиция {tok.pos[1]}"
    )


def parse_paren(parser: ExpressionParser) -> IRNode:
    """Обрабатывает '(' ... ')' — группировка или кортеж."""
    open_tok = parser.expect(TokenType.PARENTHESE_OPEN, "(")
    tok = require_not_none(parser.current(), "кортежа")
    if tok.type == TokenType.PARENTHESE_CLOSE:
        parser.advance()
        return IRTuple(pos=open_tok.pos, elements=[])

    first = parser.parse_expression()
    tok = require_not_none(parser.current())
    if tok.type == TokenType.COMMA:
        return parse_tuple(parser, open_tok.pos, first)

    else:
        parser.expect(TokenType.PARENTHESE_CLOSE, ")")
        return first


def parse_fstring(parser: ExpressionParser) -> IRFString:
    tok = parser.expect(TokenType.FORMATTED_STRING)
    _, parts = tok.data
    ir_parts = []
    for part in parts:
        if isinstance(part, str):
            ir_parts.append(part)

        else:
            sub = ExpressionParser(part)
            ir_parts.append(sub.parse())

    return IRFString(pos=tok.pos, parts=ir_parts)
