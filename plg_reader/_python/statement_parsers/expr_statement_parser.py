from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRExprStatement, IRNode
from .expressions_parser import ExpressionParser


class ExprStatementParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        if not line.tokens:
            return None

        expr = ExpressionParser(line.tokens).parse()
        return IRExprStatement(pos=expr.pos, expr=expr)
