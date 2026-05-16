from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRNode, IRPass


class PassParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or tokens[0].type != TokenType.KWORD or tokens[0].data != "pass":
            return None

        return IRPass(pos=tokens[0].pos)
