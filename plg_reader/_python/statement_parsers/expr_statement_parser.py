from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRExprStatement, IRNode
from .expressions_parser import ExpressionParser


class ExprStatementParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        if not line.tokens:
            return None

        parser = ExpressionParser(line.tokens)
        nodes = parser.parse_with_comments()
        if not nodes:
            return None

        nodes[0] = IRExprStatement(pos=nodes[0].pos, expr=nodes[0])
        return nodes
