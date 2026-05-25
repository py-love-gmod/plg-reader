from ..file_parse_dt import Line
from ..ir_builder_dt import IRFor, IRNode
from ._helpers import (
    extract_trailing_comment,
    find_colon_skip_parens,
    is_kw,
    parse_for_target,
    tokens,
)


class ForParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "for"):
            return None

        rest = t[1:]
        if not rest:
            raise SyntaxError(
                f"Ожидалось выражение после 'for' на строке {line.line_num}"
            )

        clean, comment = extract_trailing_comment(rest, 0)
        if not clean:
            raise SyntaxError(
                f"Ожидалось выражение после 'for' на строке {line.line_num}"
            )

        colon_idx = find_colon_skip_parens(clean)
        if colon_idx == -1:
            raise SyntaxError(f"Ожидалось ':' на строке {line.line_num}")

        clean = clean[:colon_idx]

        target, iter_expr = parse_for_target(clean, 0)
        nodes: list[IRNode] = [IRFor(pos=t[0].pos, target=target, iter=iter_expr)]
        if comment:
            nodes.append(comment)

        return nodes
