from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRNode, IRRaise
from ._helpers import extract_trailing_comment, is_kw, parse_expr_all, tokens


class RaiseParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "raise"):
            return None

        rest = t[1:]
        clean, comment = extract_trailing_comment(rest, 0) if rest else ([], None)

        from_idx = None
        if clean:
            from_idx = next(
                (
                    i
                    for i, tok in enumerate(clean)
                    if tok.type == TokenType.KWORD and tok.data == "from"
                ),
                None,
            )

        exc = None
        cause = None
        if from_idx is not None:
            if from_idx > 0:
                exc = parse_expr_all(clean[:from_idx])

            if from_idx + 1 < len(clean):
                cause = parse_expr_all(clean[from_idx + 1 :])

        elif clean:
            exc = parse_expr_all(clean)

        nodes: list[IRNode] = [IRRaise(pos=t[0].pos, exc=exc, cause=cause)]
        if comment:
            nodes.append(comment)

        return nodes
