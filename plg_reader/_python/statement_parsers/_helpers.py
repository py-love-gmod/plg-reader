from __future__ import annotations

from dataclasses import dataclass, field

from ..file_parse_dt import Line, Token, TokenType
from ..ir_builder_dt import IRComment, IRExceptHandler, IRNode, IRParam, IRWithItem
from .expressions_parser import ExpressionParser


@dataclass
class _ElifMarker(IRNode):
    test: IRNode


@dataclass
class _ElseMarker(IRNode):
    pass


@dataclass
class _ExceptMarker(IRNode):
    handler: IRExceptHandler


@dataclass
class _FinallyMarker(IRNode):
    pass


@dataclass
class _ElseStub(IRNode):
    body: list[IRNode] = field(default_factory=list)


@dataclass
class _FinallyStub(IRNode):
    body: list[IRNode] = field(default_factory=list)


def tokens(line: Line) -> list[Token]:
    t = line.tokens
    if not t:
        raise SyntaxError("Пустая строка не ожидалась")

    return t


def is_kw(toks: list[Token], kw: str) -> bool:
    return bool(toks and toks[0].type == TokenType.KWORD and toks[0].data == kw)


def expect_rest(tokens: list[Token], start: int, context: str) -> list[Token]:
    rest = tokens[start:]
    if not rest:
        raise SyntaxError(f"Ожидалось выражение после '{context}'")

    return rest


def parse_expr_all(tokens: list[Token]) -> IRNode:
    return ExpressionParser(tokens).parse()


def parse_name(tokens: list[Token], pos: int, context: str) -> str:
    if pos >= len(tokens) or tokens[pos].type != TokenType.NAME:
        raise SyntaxError(f"Ожидалось имя {context}")

    return tokens[pos].data


def _split_balanced(
    tokens: list[Token], line_num: int, *, allow_star: bool = False
) -> list[list[Token]]:
    """
    Разбивает список токенов по запятым верхнего уровня (вне скобок).
    Если allow_star=False, ругается на звёздочку в начале части.
    """
    parts: list[list[Token]] = []
    start = 0
    depth = 0
    for i, t in enumerate(tokens):
        if t.type == TokenType.PARENTHESE_OPEN:
            depth += 1

        elif t.type == TokenType.PARENTHESE_CLOSE:
            depth -= 1

        elif depth == 0 and t.type == TokenType.COMMA:
            part = tokens[start:i]
            if not part:
                raise SyntaxError(f"Пустая цель на строке {line_num}")

            if not allow_star and part[0].type == TokenType.OP and part[0].data == "*":
                raise SyntaxError(f"Распаковка запрещена на строке {line_num}")

            parts.append(part)
            start = i + 1

    if start < len(tokens):
        part = tokens[start:]
        if (
            part
            and not allow_star
            and part[0].type == TokenType.OP
            and part[0].data == "*"
        ):
            raise SyntaxError(f"Распаковка запрещена на строке {line_num}")

        parts.append(part)

    if not parts:
        raise SyntaxError(f"Пустая цель на строке {line_num}")

    return parts


def split_targets(tokens: list[Token], line_num: int) -> list[list[Token]]:
    return _split_balanced(tokens, line_num, allow_star=False)


def parse_params(tokens: list[Token], start: int, line_num: int) -> list[IRParam]:
    if start >= len(tokens) or tokens[start].data != "(":
        raise SyntaxError(f"Ожидалась '(' на строке {line_num}")

    depth = 1
    close_idx = -1
    for i in range(start + 1, len(tokens)):
        if tokens[i].type == TokenType.PARENTHESE_OPEN:
            depth += 1

        elif tokens[i].type == TokenType.PARENTHESE_CLOSE:
            depth -= 1
            if depth == 0:
                close_idx = i
                break

    if close_idx == -1:
        raise SyntaxError(f"Не найдена ')' в параметрах на строке {line_num}")

    inner = tokens[start + 1 : close_idx]
    if not inner:
        return []

    raw_params = _split_balanced(inner, line_num, allow_star=True)
    params: list[IRParam] = []

    for rp in raw_params:
        if not rp:
            raise SyntaxError(f"Пустой параметр на строке {line_num}")

        if rp[0].type == TokenType.OP and rp[0].data == "*":
            if len(rp) == 1:
                params.append(IRParam(pos=rp[0].pos, name="*", kind="star"))

                continue

            if len(rp) == 2 and rp[1].type == TokenType.NAME:
                params.append(IRParam(pos=rp[0].pos, name=rp[1].data, kind="star_arg"))
                continue

            raise SyntaxError(f"Некорректный * параметр на строке {line_num}")

        if rp[0].type == TokenType.OP and rp[0].data == "**":
            if len(rp) == 2 and rp[1].type == TokenType.NAME:
                params.append(IRParam(pos=rp[0].pos, name=rp[1].data, kind="kw_arg"))
                continue

            raise SyntaxError(f"Некорректный ** параметр на строке {line_num}")

        if rp[0].type == TokenType.OP and rp[0].data == "/":
            params.append(IRParam(pos=rp[0].pos, name="/", kind="slash"))
            continue

        if rp[0].type != TokenType.NAME:
            raise SyntaxError(f"Ожидалось имя параметра на строке {line_num}")

        name = rp[0].data
        rest = rp[1:]
        annotation: IRNode | None = None
        default: IRNode | None = None

        colon_idx = -1
        eq_idx = -1
        depth = 0
        for i, t in enumerate(rest):
            if t.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif t.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0:
                if t.type == TokenType.OP and t.data == ":" and colon_idx == -1:
                    colon_idx = i

                elif t.type == TokenType.OP and t.data == "=" and eq_idx == -1:
                    eq_idx = i

        if colon_idx != -1:
            annot_tokens = rest[:colon_idx]
            if annot_tokens:
                annotation = parse_expr_all(annot_tokens)

            rest = rest[colon_idx + 1 :]
            eq_idx = -1
            depth = 0
            for i, t in enumerate(rest):
                if t.type == TokenType.PARENTHESE_OPEN:
                    depth += 1

                elif t.type == TokenType.PARENTHESE_CLOSE:
                    depth -= 1

                elif depth == 0 and t.type == TokenType.OP and t.data == "=":
                    eq_idx = i
                    break

        if eq_idx != -1:
            default_tokens = rest[eq_idx + 1 :]
            if default_tokens:
                default = parse_expr_all(default_tokens)

        params.append(
            IRParam(
                pos=rp[0].pos,
                name=name,
                kind="positional",
                annotation=annotation,
                default=default,
            )
        )

    return params


def parse_bases(tokens: list[Token], start: int, line_num: int) -> list[IRNode]:
    if start >= len(tokens) or tokens[start].data != "(":
        return []

    depth = 1
    close_idx = -1
    for i in range(start + 1, len(tokens)):
        if tokens[i].type == TokenType.PARENTHESE_OPEN:
            depth += 1

        elif tokens[i].type == TokenType.PARENTHESE_CLOSE:
            depth -= 1
            if depth == 0:
                close_idx = i
                break

    if close_idx == -1:
        raise SyntaxError(f"Не найдена ')' в базовых классах на строке {line_num}")

    inner = tokens[start + 1 : close_idx]
    if not inner:
        return []

    parts = _split_balanced(inner, line_num, allow_star=False)
    return [parse_expr_all(p) for p in parts]


def parse_condition(tokens: list[Token], start: int) -> IRNode:
    return parse_expr_all(tokens[start:])


def parse_for_target(tokens: list[Token], start: int) -> tuple[IRNode, IRNode]:
    depth = 0
    in_idx = -1
    for i in range(start, len(tokens)):
        t = tokens[i]
        if t.type == TokenType.PARENTHESE_OPEN:
            depth += 1

        elif t.type == TokenType.PARENTHESE_CLOSE:
            depth -= 1

        elif depth == 0 and t.type == TokenType.KWORD and t.data == "in":
            in_idx = i
            break

    if in_idx == -1:
        raise SyntaxError("Ожидалось 'in' в заголовке for")

    target = parse_expr_all(tokens[start:in_idx])
    iter_expr = parse_expr_all(tokens[in_idx + 1 :])
    return target, iter_expr


def parse_with_items(tokens: list[Token], start: int) -> list[IRWithItem]:
    items: list[IRWithItem] = []
    i = start
    while i < len(tokens):
        depth = 0
        end = i
        while end < len(tokens):
            t = tokens[end]
            if t.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif t.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0 and t.type == TokenType.COMMA:
                break

            end += 1

        part = tokens[i:end]
        if not part:
            raise SyntaxError("Пустой элемент with")

        as_idx = -1
        for j, t in enumerate(part):
            if t.type == TokenType.KWORD and t.data == "as":
                as_idx = j
                break

        if as_idx != -1:
            context_expr = parse_expr_all(part[:as_idx])
            optional_vars = (
                parse_expr_all(part[as_idx + 1 :]) if as_idx + 1 < len(part) else None
            )

        else:
            context_expr = parse_expr_all(part)
            optional_vars = None

        items.append(
            IRWithItem(
                pos=part[0].pos, context_expr=context_expr, optional_vars=optional_vars
            )
        )
        i = end
        if i < len(tokens) and tokens[i].type == TokenType.COMMA:
            i += 1

    return items


def extract_trailing_comment(
    tokens: list[Token],
    start: int,
) -> tuple[list[Token], IRComment | None]:
    """
    Отделяет хвостовые COMMENT-токены начиная с индекса start.
    Возвращает (значимые_токены, IRComment или None).
    """
    comment_idx = next(
        (i for i in range(start, len(tokens)) if tokens[i].type == TokenType.COMMENT),
        None,
    )
    if comment_idx is not None:
        significant = tokens[:comment_idx]
        comment_tokens = tokens[comment_idx:]
        comment_node = IRComment(
            pos=comment_tokens[0].pos,
            text=" ".join(t.data for t in comment_tokens),
        )
        return significant, comment_node

    return tokens, None
