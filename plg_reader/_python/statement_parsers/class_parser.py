from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRClassDef, IRNode
from ._helpers import extract_trailing_comment, is_kw, parse_bases, parse_name, tokens


class ClassParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "class"):
            return None

        name = parse_name(t, 1, "класса")

        if len(t) > 2 and t[2].data == "(":
            depth = 1
            close_idx = -1
            for i in range(3, len(t)):
                if t[i].type == TokenType.PARENTHESE_OPEN:
                    depth += 1

                elif t[i].type == TokenType.PARENTHESE_CLOSE:
                    depth -= 1
                    if depth == 0:
                        close_idx = i
                        break

            if close_idx == -1:
                raise SyntaxError(
                    f"Не найдена ')' в базовых классах на строке {line.line_num}"
                )

            bases = parse_bases(t, 2, line.line_num)
            rest_start = close_idx + 1

        else:
            bases = []
            rest_start = 2

        _, comment = extract_trailing_comment(t, rest_start)
        nodes = [IRClassDef(pos=t[0].pos, name=name, bases=bases)]
        if comment:
            nodes.append(comment)  # pyright: ignore[reportArgumentType]

        return nodes  # pyright: ignore[reportReturnType]
