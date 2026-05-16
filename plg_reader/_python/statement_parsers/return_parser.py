from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRNode, IRReturn
from .expressions_parser import ExpressionParser


class ReturnParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if (
            not tokens
            or tokens[0].type != TokenType.KWORD
            or tokens[0].data != "return"
        ):
            return None

        start_pos = tokens[0].pos
        value = None
        if len(tokens) > 1:
            value = ExpressionParser(tokens[1:]).parse()

        return IRReturn(pos=start_pos, value=value)
