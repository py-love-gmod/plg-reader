from __future__ import annotations

from ..file_parse_dt import Line, Token, TokenType
from ..ir_builder_dt import IRNode
from .expressions_parser import ExpressionParser


def tokens(line: Line) -> list[Token]:
    """Возвращает токены строки, гарантируя, что они не пусты."""
    t = line.tokens
    if not t:
        raise SyntaxError("Пустая строка не ожидалась")

    return t


def is_kw(tokens: list[Token], kw: str) -> bool:
    """Проверяет, что первый токен — ключевое слово с заданным значением."""
    return bool(tokens and tokens[0].type == TokenType.KWORD and tokens[0].data == kw)


def expect_rest(tokens: list[Token], start: int, context: str) -> list[Token]:
    """Возвращает токены начиная с индекса start, выбрасывая ошибку, если их нет."""
    rest = tokens[start:]
    if not rest:
        raise SyntaxError(f"Ожидалось выражение после '{context}'")

    return rest


def parse_expr(tokens: list[Token], start: int, context: str = "выражения") -> IRNode:
    """Парсит выражение начиная с индекса start."""
    rest = expect_rest(tokens, start, context)
    return ExpressionParser(rest).parse()


def parse_expr_all(tokens: list[Token]) -> IRNode:
    """Парсит все токены как одно выражение."""
    return ExpressionParser(tokens).parse()


def check_forbidden_star(tokens: list[Token], context: str, line_num: int) -> None:
    """Проверяет, что первый токен не является звёздочкой (распаковкой)."""
    if tokens and tokens[0].type == TokenType.OP and tokens[0].data == "*":
        raise SyntaxError(f"Распаковка запрещена {context} на строке {line_num}")


def split_targets(tokens: list[Token], line_num: int) -> list[list[Token]]:
    """
    Разбивает список токенов на части по запятым верхнего уровня (вне скобок).
    Возвращает список токенов для каждой цели.
    Выбрасывает ошибку на пустые цели и на распаковку (звёздочку).
    """
    targets: list[list[Token]] = []
    start = 0
    depth = 0
    for i, t in enumerate(tokens):
        if t.type == TokenType.PARENTHESE_OPEN:
            depth += 1

        elif t.type == TokenType.PARENTHESE_CLOSE:
            depth -= 1

        elif depth == 0 and t.type == TokenType.COMMA:
            target_tokens = tokens[start:i]
            if not target_tokens:
                raise SyntaxError(f"Пустая цель на строке {line_num}")

            if target_tokens[0].type == TokenType.OP and target_tokens[0].data == "*":
                raise SyntaxError(f"Распаковка запрещена на строке {line_num}")

            targets.append(target_tokens)
            start = i + 1

    if start < len(tokens):
        target_tokens = tokens[start:]
        if (
            target_tokens
            and target_tokens[0].type == TokenType.OP
            and target_tokens[0].data == "*"
        ):
            raise SyntaxError(f"Распаковка запрещена на строке {line_num}")

        targets.append(target_tokens)

    if not targets:
        raise SyntaxError(f"Пустая цель на строке {line_num}")

    return targets
