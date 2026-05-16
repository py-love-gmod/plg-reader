from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRBreak, IRNode
from ._helpers import extract_trailing_comment, is_kw, tokens


class BreakParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "break"):
            return None

        _, comment = extract_trailing_comment(t, 1)
        nodes = [IRBreak(pos=t[0].pos)]
        if comment:
            nodes.append(comment)  # pyright: ignore[reportArgumentType]

        return nodes  # pyright: ignore[reportReturnType]
