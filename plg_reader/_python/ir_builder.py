from __future__ import annotations

from pathlib import Path
from typing import Type

from .file_parse_dt import Line, TokenType
from .ir_builder_dt import (
    IRClassDef,
    IRDecorator,
    IRFile,
    IRFunctionDef,
    IRIf,
    IRImport,
    IRNode,
    IRTry,
)
from .statement_parsers import (
    AssignmentParser,
    BreakParser,
    ClassParser,
    CommentParser,
    ContinueParser,
    DecoratorParser,
    DefParser,
    DeleteParser,
    ElifElseParser,
    ExceptFinallyParser,
    ExprStatementParser,
    ForParser,
    FromImportParser,
    IfParser,
    ImportParser,
    PassParser,
    RaiseParser,
    ReturnParser,
    TryParser,
    WhileParser,
    WithParser,
)
from .statement_parsers._helpers import (
    _ElifMarker,
    _ElseMarker,
    _ElseStub,
    _ExceptMarker,
    _FinallyMarker,
    _FinallyStub,
)


class IRBuilder:
    _DISPATCH: dict[str | None, Type] = {
        "def": DefParser,
        "class": ClassParser,
        "if": IfParser,
        "elif": ElifElseParser,
        "else": ElifElseParser,
        "while": WhileParser,
        "for": ForParser,
        "try": TryParser,
        "except": ExceptFinallyParser,
        "finally": ExceptFinallyParser,
        "with": WithParser,
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
        stack: list[tuple[int, list[IRNode]]] = [(0, file_node.body)]
        pending_decorators: list[IRDecorator] = []

        for line in lines:
            if not line.tokens:
                continue

            cls._close_blocks(line.indent, stack)
            if (
                line.indent > stack[-1][0]
                and stack[-1][1]
                and hasattr(stack[-1][1][-1], "body")
            ):
                cls._enter_block(line.indent, stack, line.line_num)

            nodes = cls._parse_statement(line)
            if nodes is None:
                continue

            for node in nodes:
                cls._place_node(
                    node, pending_decorators, file_node.imports, stack[-1][1]
                )

        if pending_decorators:
            raise SyntaxError("Декораторы без цели в конце файла")

        return file_node

    @staticmethod
    def _close_blocks(indent: int, stack: list[tuple[int, list[IRNode]]]) -> None:
        """Выталкиваем все уровни, чей ожидаемый отступ больше текущего."""
        while stack and indent < stack[-1][0]:
            stack.pop()

    @staticmethod
    def _enter_block(
        indent: int, stack: list[tuple[int, list[IRNode]]], line_num: int
    ) -> None:
        """Добавляем новый уровень стека, соответствующий телу последнего узла."""
        if not stack or not stack[-1][1]:
            raise SyntaxError(f"Неожиданный отступ на строке {line_num}")

        last_node = stack[-1][1][-1]
        if not hasattr(last_node, "body"):
            raise SyntaxError(f"Ожидался блок с телом на строке {line_num}")

        body: list[IRNode] = getattr(last_node, "body")
        stack.append((indent, body))

    @classmethod
    def _parse_statement(cls, line: Line) -> list[IRNode] | None:
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
            return parser.parse(line)

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
        if isinstance(node, IRImport):
            imports.append(node)
            return

        if isinstance(node, IRDecorator):
            pending_decorators.append(node)
            return

        # elif / else
        if isinstance(node, _ElifMarker):
            if not current_body or not isinstance(current_body[-1], IRIf):
                raise SyntaxError("elif без предшествующего if")

            elif_if = IRIf(pos=node.pos, test=node.test)
            current_body[-1].orelse.append(elif_if)
            current_body.append(elif_if)
            return

        if isinstance(node, _ElseMarker):
            if not current_body or not isinstance(current_body[-1], IRIf):
                raise SyntaxError("else без предшествующего if")

            stub = _ElseStub(pos=node.pos)
            current_body[-1].orelse.append(stub)
            current_body.append(stub)
            return

        # except / finally
        if isinstance(node, _ExceptMarker):
            if not current_body or not isinstance(current_body[-1], IRTry):
                raise SyntaxError("except без предшествующего try")

            current_body[-1].handlers.append(node.handler)
            current_body.append(node.handler)
            return

        if isinstance(node, _FinallyMarker):
            if not current_body or not isinstance(current_body[-1], IRTry):
                raise SyntaxError("finally без предшествующего try")

            stub = _FinallyStub(pos=node.pos)
            current_body[-1].finalbody = stub.body
            current_body.append(stub)
            return

        if pending_decorators:
            if IRBuilder._can_have_decorators(node):
                node.decorators = pending_decorators.copy()  # pyright: ignore[reportAttributeAccessIssue]
                pending_decorators.clear()

            else:
                raise SyntaxError(
                    f"Декоратор без допустимой цели на строке {node.pos[0]}"
                )

        current_body.append(node)

    @staticmethod
    def _can_have_decorators(node: IRNode) -> bool:
        return isinstance(node, (IRFunctionDef, IRClassDef))
