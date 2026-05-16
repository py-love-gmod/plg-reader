from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRDecorator, IRNode
from ._helpers import extract_trailing_comment, tokens
from .expressions_parser import ExpressionParser


class DecoratorParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not (t[0].type == TokenType.OP and t[0].data == "@"):
            return None

        rest = t[1:]
        if not rest:
            raise SyntaxError(
                f"Ожидалось выражение после '@' на строке {line.line_num}"
            )

        expr_tokens, comment = extract_trailing_comment(rest, 0)
        if not expr_tokens:
            raise SyntaxError(
                f"Ожидалось выражение после '@' на строке {line.line_num}"
            )

        expr = ExpressionParser(expr_tokens).parse()
        nodes: list[IRNode] = [IRDecorator(pos=t[0].pos, expr=expr)]
        if comment:
            nodes.append(comment)

        return nodes
