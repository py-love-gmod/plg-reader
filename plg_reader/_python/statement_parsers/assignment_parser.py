from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import (
    IRAnnotatedAssign,
    IRAssign,
    IRBinOpType,
    IRNode,
)
from ._helpers import parse_expr_all, split_targets, tokens
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
    def parse(line: Line) -> IRNode | None:
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

        if not right_tokens:
            raise SyntaxError(
                f"Пустая правая часть присваивания на строке {line.line_num}"
            )

        targets = [
            ExpressionParser(p).parse()
            for p in split_targets(left_tokens, line.line_num)
        ]
        value = ExpressionParser(right_tokens).parse()

        is_aug = op_data != "="
        aug_op = AUG_OP_MAP.get(op_data) if is_aug else None

        return IRAssign(
            pos=targets[0].pos,
            targets=targets,
            value=value,
            is_aug=is_aug,
            aug_op=aug_op,
        )

    @staticmethod
    def _parse_annotated(line: Line) -> IRNode:
        t = tokens(line)
        target = ExpressionParser([t[0]]).parse()
        rest = t[2:]

        depth = 0
        eq_idx = -1
        for i, tok in enumerate(rest):
            if tok.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif tok.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0 and tok.type == TokenType.OP and tok.data == "=":
                eq_idx = i
                break

        if eq_idx != -1:
            annotation_tokens = rest[:eq_idx]
            value_tokens = rest[eq_idx + 1 :]

        else:
            annotation_tokens = rest
            value_tokens = []

        annotation = parse_expr_all(annotation_tokens) if annotation_tokens else None
        value = parse_expr_all(value_tokens) if value_tokens else None

        return IRAnnotatedAssign(
            pos=target.pos,
            target=target,
            annotation=annotation,
            value=value,
        )
