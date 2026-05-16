from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode, IRReturn
from ._helpers import is_kw, parse_expr_all, tokens


class ReturnParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        t = tokens(line)
        if not is_kw(t, "return"):
            return None

        value = None if len(t) == 1 else parse_expr_all(t[1:])
        return IRReturn(pos=t[0].pos, value=value)
