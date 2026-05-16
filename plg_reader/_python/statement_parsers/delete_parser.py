from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRDelete, IRNode
from .expressions_parser import ExpressionParser


class DeleteParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or tokens[0].type != TokenType.KWORD or tokens[0].data != "del":
            return None

        start_pos = tokens[0].pos
        if len(tokens) < 2:
            raise SyntaxError(f"Ожидалась цель после 'del' на строке {line.line_num}")

        target = ExpressionParser(tokens[1:]).parse()
        return IRDelete(pos=start_pos, targets=[target])
