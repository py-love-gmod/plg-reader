from ..file_parse_dt import Line
from ..ir_builder_dt import IRNode, IRWhile
from ._helpers import extract_trailing_comment, is_kw, parse_condition, tokens


class WhileParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if not is_kw(t, "while"):
            return None

        rest = t[1:]
        if not rest:
            raise SyntaxError(
                f"Ожидалось условие после 'while' на строке {line.line_num}"
            )

        cond_tokens, comment = extract_trailing_comment(rest, 0)
        if not cond_tokens:
            raise SyntaxError(
                f"Ожидалось условие после 'while' на строке {line.line_num}"
            )

        test = parse_condition(cond_tokens, 0)
        nodes: list[IRNode] = [IRWhile(pos=t[0].pos, test=test)]
        if comment:
            nodes.append(comment)

        return nodes
