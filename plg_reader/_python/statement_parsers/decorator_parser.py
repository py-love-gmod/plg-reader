from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRDecorator, IRNode
from .expressions_parser import ExpressionParser


class DecoratorParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or not (tokens[0].type == TokenType.OP and tokens[0].data == "@"):
            return None

        if len(tokens) < 2:
            raise SyntaxError(
                f"Ожидалось выражение после '@' на строке {line.line_num}"
            )

        expr = ExpressionParser(tokens[1:]).parse()
        return IRDecorator(pos=tokens[0].pos, expr=expr)
