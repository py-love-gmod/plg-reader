from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRContinue, IRNode
from ._helpers import extract_trailing_comment, is_kw, tokens


class ContinueParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "continue"):
            return None

        _, comment = extract_trailing_comment(t, 1)
        nodes: list[IRNode] = [IRContinue(pos=t[0].pos)]
        if comment:
            nodes.append(comment)

        return nodes
