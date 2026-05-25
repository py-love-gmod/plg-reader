from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode, IRReturn, IRTuple
from ._helpers import (
    extract_trailing_comment,
    is_kw,
    parse_expr_all,
    split_balanced,
    tokens,
)


class ReturnParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "return"):
            return None

        rest = t[1:]
        clean, comment = extract_trailing_comment(rest, 0) if rest else ([], None)

        value = None
        if clean:
            parts = split_balanced(clean, line.line_num, allow_star=False)
            if len(parts) == 1:
                value = parse_expr_all(parts[0])

            else:
                elements = [parse_expr_all(p) for p in parts]
                value = IRTuple(pos=clean[0].pos, elements=elements)

        nodes: list[IRNode] = [IRReturn(pos=t[0].pos, value=value)]
        if comment:
            nodes.append(comment)

        return nodes
