from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRDelete, IRNode
from ._helpers import is_kw, parse_expr_all, split_targets, tokens


class DeleteParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        t = tokens(line)
        if not is_kw(t, "del"):
            return None

        rest = t[1:]
        if not rest:
            raise SyntaxError(f"Ожидалась цель после 'del' на строке {line.line_num}")

        target_exprs = [
            parse_expr_all(part) for part in split_targets(rest, line.line_num)
        ]
        return IRDelete(pos=t[0].pos, targets=target_exprs)
