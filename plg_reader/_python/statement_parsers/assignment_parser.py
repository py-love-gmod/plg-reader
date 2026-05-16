from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import (
    IRAnnotatedAssign,
    IRAssign,
    IRBinOpType,
    IRNode,
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
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens:
            return None

        if (
            len(tokens) >= 2
            and tokens[0].type == TokenType.NAME
            and tokens[1].type == TokenType.OP
            and tokens[1].data == ":"
        ):
            return AssignmentParser._parse_annotated(line)

        depth = 0
        eq_idx = -1
        op_data = None
        for i, t in enumerate(tokens):
            if t.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif t.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0 and t.type == TokenType.OP:
                if t.data in AUG_OP_MAP or t.data == "=":
                    eq_idx = i
                    op_data = t.data
                    break

        if eq_idx == -1:
            return None

        op_data = tokens[eq_idx].data

        if op_data == ":=":
            raise SyntaxError(
                f"Walrus-оператор (:=) не поддерживается на строке {line.line_num}"
            )

        left_tokens = tokens[:eq_idx]
        right_tokens = tokens[eq_idx + 1 :]

        if not left_tokens:
            raise SyntaxError(...)

        if not right_tokens:
            raise SyntaxError(...)

        targets = AssignmentParser._parse_targets(left_tokens, line.line_num)
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
    def _parse_targets(tokens: list, line_num: int) -> list[IRNode]:
        """Разбивает список токенов по запятым верхнего уровня и каждую часть парсит ExpressionParser'ом."""
        targets = []
        start = 0
        depth = 0
        for i, t in enumerate(tokens):
            if t.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif t.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0 and t.type == TokenType.COMMA:
                target_tokens = tokens[start:i]
                if not target_tokens:
                    raise SyntaxError(
                        f"Пустая цель в присваивании на строке {line_num}"
                    )

                if (
                    target_tokens[0].type == TokenType.OP
                    and target_tokens[0].data == "*"
                ):
                    raise SyntaxError(
                        f"Распаковка в целях присваивания запрещена на строке {line_num}"
                    )

                targets.append(ExpressionParser(target_tokens).parse())
                start = i + 1

        if start < len(tokens):
            target_tokens = tokens[start:]
            if (
                target_tokens
                and target_tokens[0].type == TokenType.OP
                and target_tokens[0].data == "*"
            ):
                raise SyntaxError(
                    f"Распаковка в целях присваивания запрещена на строке {line_num}"
                )

            targets.append(ExpressionParser(target_tokens).parse())

        if not targets:
            raise SyntaxError(f"Пустая левая часть присваивания на строке {line_num}")

        return targets

    @staticmethod
    def _parse_annotated(line: Line) -> IRNode:
        tokens = line.tokens
        target = ExpressionParser([tokens[0]]).parse()
        rest = tokens[2:]

        depth = 0
        eq_idx = -1
        for i, t in enumerate(rest):
            if t.type == TokenType.PARENTHESE_OPEN:
                depth += 1

            elif t.type == TokenType.PARENTHESE_CLOSE:
                depth -= 1

            elif depth == 0 and t.type == TokenType.OP and t.data == "=":
                eq_idx = i
                break

        if eq_idx != -1:
            annotation_tokens = rest[:eq_idx]
            value_tokens = rest[eq_idx + 1 :]

        else:
            annotation_tokens = rest
            value_tokens = []

        annotation = (
            ExpressionParser(annotation_tokens).parse() if annotation_tokens else None
        )
        value = ExpressionParser(value_tokens).parse() if value_tokens else None

        return IRAnnotatedAssign(
            pos=target.pos,
            target=target,
            annotation=annotation,
            value=value,
        )
