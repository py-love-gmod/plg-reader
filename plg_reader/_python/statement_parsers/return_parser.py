from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode, IRReturn
from ._helpers import extract_trailing_comment, is_kw, parse_expr_all, tokens


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
            value = parse_expr_all(clean)

        nodes: list[IRNode] = [IRReturn(pos=t[0].pos, value=value)]
        if comment:
            nodes.append(comment)

        return nodes
