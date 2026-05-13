from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRConstant, IRFString, IRName, IRNode
from .base import ExpressionParser


def parse_atom(parser: ExpressionParser) -> IRNode:
    tok = parser.current()
    if tok is None:
        raise SyntaxError("Неожиданный конец выражения")

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
        return parse_paren(parser)

    if tok.type == TokenType.PARENTHESE_CLOSE:
        raise SyntaxError(
            f"Неожиданная закрывающая скобка на строке {tok.pos[0]}, позиция {tok.pos[1]}"
        )

    raise SyntaxError(
        f"Неожиданный токен {tok.data} на строке {tok.pos[0]}, позиция {tok.pos[1]}"
    )


def parse_paren(parser: ExpressionParser) -> IRNode:
    parser.expect(TokenType.PARENTHESE_OPEN, "(")
    cur = parser.current()
    if cur is not None and cur.type == TokenType.PARENTHESE_CLOSE:
        parser.advance()
        raise SyntaxError(
            f"Пустые скобки не поддерживаются на строке {cur.pos[0]}, позиция {cur.pos[1]}"
        )

    inner = parser.parse_expression()
    parser.expect(TokenType.PARENTHESE_CLOSE, ")")
    return inner


def parse_fstring(parser: ExpressionParser) -> IRFString:
    tok = parser.expect(TokenType.FORMATTED_STRING)
    _, parts = tok.data  # parts: list[str | list[Token]]
    ir_parts = []
    for part in parts:
        if isinstance(part, str):
            ir_parts.append(part)

        else:
            sub = ExpressionParser(part)
            ir_parts.append(sub.parse())

    return IRFString(pos=tok.pos, parts=ir_parts)
