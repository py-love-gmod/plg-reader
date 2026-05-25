from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode, IRWith
from ._helpers import (
    extract_trailing_comment,
    find_colon_skip_parens,
    is_kw,
    parse_with_items,
    tokens,
)


class WithParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "with"):
            return None

        rest = t[1:]
        if not rest:
            raise SyntaxError(
                f"Ожидалось выражение после 'with' на строке {line.line_num}"
            )

        clean, comment = extract_trailing_comment(rest, 0)
        if not clean:
            raise SyntaxError(
                f"Ожидалось выражение после 'with' на строке {line.line_num}"
            )

        colon_idx = find_colon_skip_parens(clean)
        if colon_idx == -1:
            raise SyntaxError(f"Ожидалось ':' на строке {line.line_num}")

        clean = clean[:colon_idx]

        items = parse_with_items(clean, 0)
        nodes: list[IRNode] = [IRWith(pos=t[0].pos, items=items)]
        if comment:
            nodes.append(comment)

        return nodes
