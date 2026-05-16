from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import (
    IRConstant,
    IRFString,
    IRFStringDebug,
    IRName,
    IRNode,
    IRTuple,
)
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
        prefix, s = tok.data
        return IRConstant(pos=tok.pos, value=s, prefix=prefix)

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
    prefix, parts = tok.data
    ir_parts = []
    for part in parts:
        if isinstance(part, str):
            ir_parts.append(part)

        else:
            sub = type(parser)(part)
            expr_node = sub.parse_expression()
            cur = sub.current()
            if cur is not None and cur.type == TokenType.OP and cur.data == "=":
                sub.advance()
                if sub.current() is not None:
                    raise SyntaxError(
                        f"Неожиданный токен после '=' в f-строке на строке {cur.pos[0]}, позиция {cur.pos[1]}"
                    )
                ir_parts.append(IRFStringDebug(pos=expr_node.pos, expr=expr_node))

            else:
                ir_parts.append(expr_node)

    return IRFString(pos=tok.pos, prefix=prefix, parts=ir_parts)
