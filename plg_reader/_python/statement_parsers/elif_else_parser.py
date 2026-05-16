from dataclasses import dataclass

from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode
from ._helpers import extract_trailing_comment, is_kw, parse_condition, tokens


@dataclass
class _ElifMarker(IRNode):
    test: IRNode


@dataclass
class _ElseMarker(IRNode):
    pass


class ElifElseParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if is_kw(t, "elif"):
            rest = t[1:]
            if not rest:
                raise SyntaxError(
                    f"Ожидалось условие после 'elif' на строке {line.line_num}"
                )

            cond_tokens, comment = extract_trailing_comment(rest, 0)
            if not cond_tokens:
                raise SyntaxError(
                    f"Ожидалось условие после 'elif' на строке {line.line_num}"
                )

            test = parse_condition(cond_tokens, 0)
            nodes: list[IRNode] = [_ElifMarker(pos=t[0].pos, test=test)]
            if comment:
                nodes.append(comment)

            return nodes

        elif is_kw(t, "else"):
            _, comment = extract_trailing_comment(t, 1)
            nodes: list[IRNode] = [_ElseMarker(pos=t[0].pos)]
            if comment:
                nodes.append(comment)

            return nodes

        return None
