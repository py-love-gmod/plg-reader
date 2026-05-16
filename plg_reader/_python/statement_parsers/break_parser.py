from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRBreak, IRNode


class BreakParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or tokens[0].type != TokenType.KWORD or tokens[0].data != "break":
            return None

        return IRBreak(pos=tokens[0].pos)
