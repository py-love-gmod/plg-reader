from __future__ import annotations

from ...file_parse_dt import Token, TokenType


def require_not_none(tok: Token | None, context: str = "выражении") -> Token:
    """Проверяет, что токен не None, иначе выбрасывает SyntaxError."""
    if tok is None:
        raise SyntaxError(f"Неожиданный конец {context}")

    return tok


def forbid_star(tok: Token, context: str = "выражении") -> None:
    """Запрещает распаковку (* или **)."""
    if tok.type == TokenType.OP and tok.data in ("*", "**"):
        raise SyntaxError(
            f"Распаковка запрещена {context} на строке {tok.pos[0]}, позиция {tok.pos[1]}"
        )
