from __future__ import annotations

from pathlib import Path
from typing import Type

from .file_parse_dt import Line, TokenType
from .ir_builder_dt import (
    IRClassDef,
    IRDecorator,
    IRFile,
    IRFunctionDef,
    IRImport,
    IRNode,
)
from .statement_parsers import (
    AssignmentParser,
    BreakParser,
    CommentParser,
    ContinueParser,
    DecoratorParser,
    DeleteParser,
    ExprStatementParser,
    FromImportParser,
    ImportParser,
    PassParser,
    RaiseParser,
    ReturnParser,
)


class IRBuilder:
    _DISPATCH: dict[str | None, Type] = {
        "return": ReturnParser,
        "del": DeleteParser,
        "raise": RaiseParser,
        "pass": PassParser,
        "break": BreakParser,
        "continue": ContinueParser,
        "import": ImportParser,
        "from": FromImportParser,
        "@": DecoratorParser,
        None: AssignmentParser,
    }

    @classmethod
    def build(cls, lines: list[Line], file_path: Path) -> IRFile:
        file_node = IRFile(pos=(1, 0), path=file_path)
        stack: list[tuple[int, list[IRNode]]] = [(-1, file_node.body)]
        pending_decorators: list[IRDecorator] = []

        for line in lines:
            tokens = line.tokens
            if not tokens:
                continue

            cls._close_blocks(line.indent, stack)
            if line.indent > stack[-1][0]:
                cls._enter_block(line.indent, stack, line.line_num)

            node = cls._parse_statement(line)
            if node is None:
                continue

            cls._place_node(node, pending_decorators, file_node.imports, stack[-1][1])

        if pending_decorators:
            raise SyntaxError("Декораторы без цели в конце файла")

        return file_node

    @staticmethod
    def _close_blocks(indent: int, stack: list[tuple[int, list[IRNode]]]) -> None:
        """Выбрасывает из стека все блоки с уровнем отступа больше текущего."""
        while stack and indent < stack[-1][0]:
            stack.pop()

    @staticmethod
    def _enter_block(
        indent: int,
        stack: list[tuple[int, list[IRNode]]],
        line_num: int,
    ) -> None:
        if not stack or not stack[-1][1]:
            raise SyntaxError(f"Неожиданный отступ на строке {line_num}")

        last_node = stack[-1][1][-1]
        if not hasattr(last_node, "body"):
            raise SyntaxError(f"Ожидался блок с телом на строке {line_num}")

        body: list[IRNode] = getattr(last_node, "body")
        stack.append((indent, body))

    @classmethod
    def _parse_statement(cls, line: Line) -> IRNode | None:
        tokens = line.tokens
        first = tokens[0]

        if first.type == TokenType.COMMENT:
            return CommentParser.parse(line)

        if first.type == TokenType.KWORD:
            key: str | None = first.data

        elif first.type == TokenType.OP and first.data == "@":
            key = "@"

        else:
            key = None

        parser = cls._DISPATCH.get(key)
        if parser is not None:
            node = parser.parse(line)
            if node is not None:
                return node

        if key is None:
            return ExprStatementParser.parse(line)

        return None

    @staticmethod
    def _place_node(
        node: IRNode,
        pending_decorators: list[IRDecorator],
        imports: list[IRImport],
        current_body: list[IRNode],
    ) -> None:
        """
        Помещает распарсенный узел в правильную часть IRFile:
        - импорты → в imports,
        - декораторы → накапливаются в pending_decorators,
        - остальные узлы → в current_body (с предварительным прикреплением декораторов).
        """
        if isinstance(node, IRImport):
            imports.append(node)
            return

        if isinstance(node, IRDecorator):
            pending_decorators.append(node)
            return

        if pending_decorators:
            if IRBuilder._can_have_decorators(node):
                node.decorators = pending_decorators.copy()  # type: ignore[attr-defined]
                pending_decorators.clear()

            else:
                raise SyntaxError(
                    f"Декоратор без допустимой цели на строке {node.pos[0]}"
                )

        current_body.append(node)

    @staticmethod
    def _can_have_decorators(node: IRNode) -> bool:
        return isinstance(node, (IRFunctionDef, IRClassDef))
