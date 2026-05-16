from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import (
    IRAnnotatedAssign,
    IRAssign,
    IRBinOpType,
    IRNode,
    IRTuple,
)
from ._helpers import (
    _split_balanced,
    extract_trailing_comment,
    parse_expr_all,
    split_targets,
    tokens,
)
from .expressions_parser import ExpressionParser

AUG_OP_MAP = {
    "+=": IRBinOpType.ADD,
    "-=": IRBinOpType.SUB,
    "*=": IRBinOpType.MUL,
    "/=": IRBinOpType.DIV,
    "//=": IRBinOpType.FLOORDIV,
    "%=": IRBinOpType.MOD,
    "**=": IRBinOpType.POW,
    "&=": IRBinOpType.BIT_AND,
    "|=": IRBinOpType.BIT_OR,
    "^=": IRBinOpType.BIT_XOR,
    "<<=": IRBinOpType.LSHIFT,
    ">>=": IRBinOpType.RSHIFT,
}


class AssignmentParser:
    @staticmethod
    def parse(line: Line) -> list[IRNode] | None:
        t = tokens(line)

        if (
            len(t) >= 2
            and t[0].type == TokenType.NAME
            and t[1].type == TokenType.OP
            and t[1].data == ":"
        ):
            return AssignmentParser._parse_annotated(line)

        depth = 0
        eq_idx = -1
        for i, tok in enumerate(t):
            if tok.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif tok.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif (
                depth == 0
                and tok.type == TokenType.OP
                and (tok.data in AUG_OP_MAP or tok.data == "=")
            ):
                eq_idx = i
                break

        if eq_idx == -1:
            return None

        op_data = t[eq_idx].data
        if op_data == ":=":
            raise SyntaxError(
                f"Walrus-оператор (:=) не поддерживается на строке {line.line_num}"
            )

        left_tokens = t[:eq_idx]
        right_tokens = t[eq_idx + 1 :]

        if not left_tokens:
            raise SyntaxError(
                f"Пустая левая часть присваивания на строке {line.line_num}"
            )

        right_significant, comment = extract_trailing_comment(right_tokens, 0)
        if not right_significant:
            raise SyntaxError(
                f"Пустая правая часть присваивания на строке {line.line_num}"
            )

        left_parts = split_targets(left_tokens, line.line_num)
        targets = [ExpressionParser(p).parse() for p in left_parts]
        right_parts = _split_balanced(
            right_significant, line.line_num, allow_star=False
        )
        if len(right_parts) == 1:
            value = ExpressionParser(right_significant).parse()

        else:
            elements = [ExpressionParser(p).parse() for p in right_parts]
            value = IRTuple(pos=elements[0].pos, elements=elements)

        is_aug = op_data != "="
        aug_op = AUG_OP_MAP.get(op_data) if is_aug else None
        nodes = [
            IRAssign(
                pos=targets[0].pos,
                targets=targets,
                value=value,
                is_aug=is_aug,
                aug_op=aug_op,
            )
        ]

        if comment:
            nodes.append(comment)  # pyright: ignore[reportArgumentType]

        return nodes  # pyright: ignore[reportReturnType]

    @staticmethod
    def _parse_annotated(line: Line) -> list[IRNode] | None:
        t = tokens(line)
        target = ExpressionParser([t[0]]).parse()
        rest = t[2:]

        significant, comment = extract_trailing_comment(rest, 0)
        depth = 0
        eq_idx = -1
        for i, tok in enumerate(significant):
            if tok.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif tok.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0 and tok.type == TokenType.OP and tok.data == "=":
                eq_idx = i
                break

        if eq_idx != -1:
            annotation_tokens = significant[:eq_idx]
            value_tokens = significant[eq_idx + 1 :]

        else:
            annotation_tokens = significant
            value_tokens = []

        annotation = parse_expr_all(annotation_tokens) if annotation_tokens else None
        value = parse_expr_all(value_tokens) if value_tokens else None
        nodes = [
            IRAnnotatedAssign(
                pos=target.pos,
                target=target,
                annotation=annotation,
                value=value,
            )
        ]

        if comment:
            nodes.append(comment)  # pyright: ignore[reportArgumentType]

        return nodes  # pyright: ignore[reportReturnType]
