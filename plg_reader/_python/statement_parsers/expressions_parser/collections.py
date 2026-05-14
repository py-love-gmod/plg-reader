from __future__ import annotations

from ...file_parse_dt import TokenType
from ...ir_builder_dt import (
    IRDict,
    IRDictItem,
    IRList,
    IRNode,
    IRSet,
    IRTuple,
)
from .base import ExpressionParser
from .utils import forbid_star, require_not_none


def parse_list(parser: ExpressionParser, open_pos: tuple[int, int]) -> IRList:
    """'[' [items] ']'"""
    elements = _parse_items(parser, TokenType.PARENTHESE_CLOSE, "]")
    return IRList(pos=open_pos, elements=elements)


def parse_tuple(
    parser: ExpressionParser,
    open_pos: tuple[int, int],
    first: IRNode | None = None,
) -> IRTuple:
    """
    '(' [items] ')'
    Если first передан, значит первый элемент уже разобран (используется из parse_paren).
    """
    if first is None:
        elements = _parse_items(parser, TokenType.PARENTHESE_CLOSE, ")")

    else:
        elements = [first]
        tok = parser.current()
        while tok is not None and tok.type == TokenType.COMMA:
            parser.advance()
            tok = parser.current()
            if tok is not None and tok.type == TokenType.PARENTHESE_CLOSE:
                break

            elements.append(parser.parse_expression())
            tok = parser.current()

        parser.expect(TokenType.PARENTHESE_CLOSE, ")")

    return IRTuple(pos=open_pos, elements=elements)


def parse_set(parser: ExpressionParser, open_pos: tuple[int, int]) -> IRSet:
    """'{' [items] '}'"""
    elements = _parse_items(parser, TokenType.PARENTHESE_CLOSE, "}")
    return IRSet(pos=open_pos, elements=elements)


def parse_dict(parser: ExpressionParser, open_pos: tuple[int, int]) -> IRDict:
    """
    '{' [key ':' value (',' key ':' value)*] '}'
    Открывающая скобка уже съедена.
    """
    items: list[IRDictItem] = []
    tok = parser.current()
    if tok is not None and tok.type == TokenType.PARENTHESE_CLOSE and tok.data == "}":
        parser.advance()
        return IRDict(pos=open_pos, items=items)

    while True:
        tok = require_not_none(parser.current(), "словаре")
        forbid_star(tok, "в словаре")

        key = parser.parse_expression()
        parser.expect(TokenType.OP, ":")
        value = parser.parse_expression()
        items.append(IRDictItem(pos=key.pos, key=key, value=value))

        tok = parser.current()
        if tok is not None and tok.type == TokenType.COMMA:
            parser.advance()
            tok = parser.current()
            if (
                tok is not None
                and tok.type == TokenType.PARENTHESE_CLOSE
                and tok.data == "}"
            ):
                parser.advance()
                break

        else:
            break

    parser.expect(TokenType.PARENTHESE_CLOSE, "}")
    return IRDict(pos=open_pos, items=items)


def parse_brace_collection(
    parser: ExpressionParser, open_pos: tuple[int, int]
) -> IRNode:
    """
    Пытается разобрать как словарь, при неудаче — как множество.
    Открывающая скобка уже съедена.
    """
    start = parser.pos
    try:
        return parse_dict(parser, open_pos)

    except SyntaxError:
        parser.pos = start
        return parse_set(parser, open_pos)


def _parse_items(
    parser: ExpressionParser, end_type: TokenType, end_val: str
) -> list[IRNode]:
    """
    Общий сбор элементов через запятую до закрывающей скобки.
    Используется для списков, множеств и кортежей (без первого элемента).
    """
    items: list[IRNode] = []
    tok = parser.current()
    if tok is not None and tok.type == end_type and tok.data == end_val:
        parser.advance()
        return items

    while True:
        tok = require_not_none(parser.current(), "коллекции")
        forbid_star(tok, "в коллекции")
        items.append(parser.parse_expression())

        tok = parser.current()
        if tok is not None and tok.type == TokenType.COMMA:
            parser.advance()
            tok = parser.current()
            if tok is not None and tok.type == end_type and tok.data == end_val:
                parser.advance()
                break

        else:
            break

    parser.expect(end_type, end_val)
    return items
