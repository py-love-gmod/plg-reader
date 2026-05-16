from dataclasses import dataclass

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRExceptHandler, IRNode
from ._helpers import (
    extract_trailing_comment,
    is_kw,
    parse_expr_all,
    parse_name,
    tokens,
)


@dataclass
class _ExceptMarker(IRNode):
    handler: IRExceptHandler


@dataclass
class _FinallyMarker(IRNode):
    pass


class ExceptFinallyParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        if is_kw(t, "except"):
            rest = t[1:]
            if not rest:
                raise SyntaxError(
                    f"Ожидалось выражение после 'except' на строке {line.line_num}"
                )

            significant, comment = extract_trailing_comment(rest, 0)

            typ = None
            name = None
            if significant:
                as_idx = -1
                depth = 0
                for i, tok in enumerate(significant):
                    if tok.type == TokenType.PARENTHESE_OPEN:
                        depth += 1

                    elif tok.type == TokenType.PARENTHESE_CLOSE:
                        depth -= 1

                    elif (
                        depth == 0 and tok.type == TokenType.KWORD and tok.data == "as"
                    ):
                        as_idx = i
                        break

                if as_idx != -1:
                    if as_idx > 0:
                        typ = parse_expr_all(significant[:as_idx])

                    name = parse_name(significant, as_idx + 1, "псевдонима исключения")

                else:
                    typ = parse_expr_all(significant)

            handler = IRExceptHandler(pos=t[0].pos, type=typ, name=name)
            nodes: list[IRNode] = [_ExceptMarker(pos=t[0].pos, handler=handler)]
            if comment:
                nodes.append(comment)

            return nodes

        elif is_kw(t, "finally"):
            _, comment = extract_trailing_comment(t, 1)
            nodes: list[IRNode] = [_FinallyMarker(pos=t[0].pos)]
            if comment:
                nodes.append(comment)

            return nodes

        elif is_kw(t, "else"):
            return None

        return None
