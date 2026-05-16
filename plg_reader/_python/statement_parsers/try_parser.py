from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode, IRTry
from ._helpers import extract_trailing_comment, is_kw, tokens


class TryParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "try"):
            return None

        _, comment = extract_trailing_comment(t, 1)
        nodes: list[IRNode] = [IRTry(pos=t[0].pos)]
        if comment:
            nodes.append(comment)

        return nodes
