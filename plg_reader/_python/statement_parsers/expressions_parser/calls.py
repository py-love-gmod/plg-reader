from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import IRCall, IRNode
from .base import ExpressionParser


def parse_call(parser: ExpressionParser, func: IRNode) -> IRCall:
    """Парсит вызов: func '(' [arguments] ')'"""
    parser.expect(TokenType.PARENTHESE_OPEN, "(")

    args: list[IRNode] = []
    kwargs: dict[str, IRNode] = {}

    tok = parser.current()
    if tok is not None and tok.type == TokenType.PARENTHESE_CLOSE:
        parser.advance()
        return IRCall(pos=func.pos, func=func)

    while True:
        tok = parser.current()
        if tok is None:
            raise SyntaxError("Неожиданный конец в аргументах вызова")

        if tok.type == TokenType.NAME:
            start_pos = parser.pos
            name = parser.advance().data  # pyright: ignore[reportOptionalMemberAccess] # гарантированно не None, т.к. проверено
            eq_tok = parser.current()
            if (
                eq_tok is not None
                and eq_tok.type == TokenType.OP
                and eq_tok.data == "="
            ):
                parser.advance()  #
                value = parser.parse_expression()
                kwargs[name] = value

            else:
                parser.pos = start_pos
                args.append(parser.parse_expression())

        else:
            args.append(parser.parse_expression())

        tok = parser.current()
        if tok is not None and tok.type == TokenType.COMMA:
            parser.advance()
            tok = parser.current()
            if tok is not None and tok.type == TokenType.PARENTHESE_CLOSE:
                parser.advance()
                break

        else:
            break

    parser.expect(TokenType.PARENTHESE_CLOSE, ")")
    return IRCall(pos=func.pos, func=func, args=args, kwargs=kwargs)
