from __future__ import annotations

from pathlib import Path
from typing import Type

from .file_parse_dt import Line
from .ir_builder_dt import (
    IRClassDef,
    IRDecorator,
    IRFile,
    IRFunctionDef,
    IRNode,
)


class IRBuilder:
    """
    Строит IR-дерево файла из линейного списка Line (результат FileParser).

    Парсеры конкретных операторов регистрируются в _statement_parsers.
    Каждый парсер – это класс со статическим методом:

        @staticmethod
        def parse(line: Line) -> IRNode | None:
            ...

    Порядок парсеров в списке важен: более специфичные должны идти раньше.
    """

    _statement_parsers: list[Type] = []

    @classmethod
    def build(cls, lines: list[Line], file_path: Path) -> IRFile:
        """Основной метод сборки IR-представления файла."""
        file_node = IRFile(pos=(1, 0), path=file_path)
        stack: list[tuple[int, list[IRNode]]] = [(-1, file_node.body)]
        pending_decorators: list[IRDecorator] = []

        for line in lines:
            tokens = line.tokens
            if not tokens:
                continue

            indent = line.indent
            cls._close_blocks(indent, stack)
            current_indent, current_list = stack[-1]

            if indent > current_indent:
                cls._enter_block(indent, stack, line.line_num)
                current_indent, current_list = stack[-1]

            parsed_node = cls._parse_statement(line)
            if isinstance(parsed_node, IRDecorator):
                pending_decorators.append(parsed_node)
                continue

            if pending_decorators:
                if parsed_node is not None and cls._can_have_decorators(parsed_node):
                    parsed_node.decorators = pending_decorators  # type: ignore[attr-defined]
                    pending_decorators.clear()

                else:
                    raise SyntaxError(
                        f"Декоратор без допустимой цели на строке {line.line_num}"
                    )

            if parsed_node is not None:
                current_list.append(parsed_node)

        if pending_decorators:
            raise SyntaxError("Декораторы без цели в конце файла")

        return file_node

    @staticmethod
    def _close_blocks(indent: int, stack: list[tuple[int, list[IRNode]]]) -> None:
        while stack and indent < stack[-1][0]:
            stack.pop()

    @staticmethod
    def _enter_block(
        indent: int,
        stack: list[tuple[int, list[IRNode]]],
        line_num: int,
    ) -> None:
        if not stack:
            raise SyntaxError(f"Неожиданный отступ на строке {line_num}")

        last_node = stack[-1][1][-1] if stack[-1][1] else None
        if last_node is None or not hasattr(last_node, "body"):
            raise SyntaxError(f"Ожидался блок с телом на строке {line_num}")

        stack.append((indent, last_node.body))  # type: ignore[attr-defined]

    @classmethod
    def _parse_statement(cls, line: Line) -> IRNode | None:
        for parser_cls in cls._statement_parsers:
            node = parser_cls.parse(line)
            if node is not None:
                return node

        return None

    @staticmethod
    def _can_have_decorators(node: IRNode) -> bool:
        return isinstance(node, (IRFunctionDef, IRClassDef))
