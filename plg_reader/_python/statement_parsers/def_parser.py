from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRFunctionDef, IRNode
from ._helpers import (
    extract_trailing_comment,
    is_kw,
    parse_expr_all,
    parse_name,
    parse_params,
    tokens,
)


class DefParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "def"):
            return None

        name = parse_name(t, 1, "функции")
        params = parse_params(t, 2, line.line_num)

        depth = 1
        close_paren_idx = -1
        for i in range(3, len(t)):
            if t[i].type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif t[i].type == TokenType.PARENTHESE_CLOSE:
                depth -= 1
                if depth == 0:
                    close_paren_idx = i
                    break

        if close_paren_idx == -1:
            raise SyntaxError(f"Не найдена ')' в параметрах на строке {line.line_num}")

        rest_tokens = t[close_paren_idx + 1 :]
        significant, comment = extract_trailing_comment(rest_tokens, 0)

        returns = None
        if (
            significant
            and significant[0].type == TokenType.OP
            and significant[0].data == "->"
        ):
            return_tokens = significant[1:]
            if return_tokens:
                returns = parse_expr_all(return_tokens)

        nodes: list[IRNode] = [
            IRFunctionDef(pos=t[0].pos, name=name, params=params, returns=returns)
        ]
        if comment:
            nodes.append(comment)

        return nodes
