from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRNode, IRRaise
from .expressions_parser import ExpressionParser


class RaiseParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or tokens[0].type != TokenType.KWORD or tokens[0].data != "raise":
            return None

        start_pos = tokens[0].pos
        exc = None
        cause = None

        from_idx = -1
        for i, t in enumerate(tokens):
            if t.type == TokenType.KWORD and t.data == "from":
                from_idx = i
                break

        if from_idx != -1:
            if from_idx > 1:
                exc = ExpressionParser(tokens[1:from_idx]).parse()
                
            if from_idx + 1 < len(tokens):
                cause = ExpressionParser(tokens[from_idx + 1 :]).parse()
                
        elif len(tokens) > 1:
            exc = ExpressionParser(tokens[1:]).parse()

        return IRRaise(pos=start_pos, exc=exc, cause=cause)
