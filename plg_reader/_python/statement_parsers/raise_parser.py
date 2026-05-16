from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRNode, IRRaise
from ._helpers import is_kw, parse_expr_all, tokens


class RaiseParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        t = tokens(line)
        if not is_kw(t, "raise"):
            return None

        from_idx = next(
            (
                i
                for i, tok in enumerate(t)
                if tok.type == TokenType.KWORD and tok.data == "from"
            ),
            None,
        )

        if from_idx is not None:
            exc = parse_expr_all(t[1:from_idx]) if from_idx > 1 else None
            cause = parse_expr_all(t[from_idx + 1 :]) if from_idx + 1 < len(t) else None

        else:
            exc = parse_expr_all(t[1:]) if len(t) > 1 else None
            cause = None

        return IRRaise(pos=t[0].pos, exc=exc, cause=cause)
