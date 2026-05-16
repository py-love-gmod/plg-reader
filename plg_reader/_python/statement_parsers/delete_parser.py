from __future__ import annotations

from ..file_parse_dt import Line
from ..ir_builder_dt import IRDelete, IRNode
from ._helpers import (
    extract_trailing_comment,
    is_kw,
    parse_expr_all,
    split_targets,
    tokens,
)


class DeleteParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "del"):
            return None

        rest = t[1:]
        if not rest:
            raise SyntaxError(f"Ожидалась цель после 'del' на строке {line.line_num}")

        targets_tokens, comment = extract_trailing_comment(rest, 0)
        if not targets_tokens:
            raise SyntaxError(f"Ожидалась цель после 'del' на строке {line.line_num}")

        target_exprs = [
            parse_expr_all(part)
            for part in split_targets(targets_tokens, line.line_num)
        ]
        nodes: list[IRNode] = [IRDelete(pos=t[0].pos, targets=target_exprs)]
        if comment:
            nodes.append(comment)

        return nodes
