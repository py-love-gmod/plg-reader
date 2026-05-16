from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRImport, IRNode


class ImportParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if (
            not tokens
            or tokens[0].type != TokenType.KWORD
            or tokens[0].data != "import"
        ):
            return None
        if len(tokens) < 2:
            raise SyntaxError(
                f"Ожидалось имя модуля после 'import' на строке {line.line_num}"
            )

        rest = tokens[1:]
        modules: list[str] = []
        names: list[str | tuple[str, str]] = []

        ImportParser._collect_imports(rest, modules, names)

        return IRImport(
            pos=tokens[0].pos,
            modules=modules,
            names=names,
            is_from=False,
            level=0,
        )

    @staticmethod
    def _collect_imports(
        tokens: list, modules: list[str], names: list[str | tuple[str, str]]
    ) -> None:
        i = 0
        while i < len(tokens):
            if tokens[i].type != TokenType.NAME:
                raise SyntaxError(f"Ожидалось имя модуля, получено {tokens[i].data}")

            mod_parts = [tokens[i].data]
            i += 1
            while i < len(tokens) and tokens[i].type == TokenType.DOT:
                i += 1
                if i >= len(tokens) or tokens[i].type != TokenType.NAME:
                    raise SyntaxError("Ожидалось имя после '.' в импорте")

                mod_parts.append(tokens[i].data)
                i += 1

            full_mod = ".".join(mod_parts)
            modules.append(full_mod)

            if (
                i < len(tokens)
                and tokens[i].type == TokenType.KWORD
                and tokens[i].data == "as"
            ):
                i += 1
                if i >= len(tokens) or tokens[i].type != TokenType.NAME:
                    raise SyntaxError("Ожидалось имя после 'as'")

                alias = tokens[i].data
                names.append((full_mod, alias))
                i += 1

            else:
                names.append(full_mod)

            if i < len(tokens) and tokens[i].type == TokenType.COMMA:
                i += 1

            elif i < len(tokens):
                raise SyntaxError(f"Неожиданный токен {tokens[i].data} в импорте")

            else:
                break


class FromImportParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or tokens[0].type != TokenType.KWORD or tokens[0].data != "from":
            return None

        i = 1
        level = 0
        while i < len(tokens) and tokens[i].type == TokenType.DOT:
            level += 1
            i += 1

        modules: list[str] = []
        if i < len(tokens) and tokens[i].type == TokenType.NAME:
            mod_parts = [tokens[i].data]
            i += 1
            while i < len(tokens) and tokens[i].type == TokenType.DOT:
                i += 1
                if i >= len(tokens) or tokens[i].type != TokenType.NAME:
                    raise SyntaxError("Ожидалось имя после '.' в импорте")

                mod_parts.append(tokens[i].data)
                i += 1

            modules.append(".".join(mod_parts))

        elif (
            i < len(tokens) and tokens[i].type == TokenType.OP and tokens[i].data == "*"
        ):
            raise SyntaxError("Импорт звёздочки (*) не поддерживается")

        if (
            i >= len(tokens)
            or tokens[i].type != TokenType.KWORD
            or tokens[i].data != "import"
        ):
            raise SyntaxError("Ожидалось 'import' после 'from'")

        i += 1

        if i >= len(tokens):
            raise SyntaxError("Ожидались имена после 'import'")

        names: list[str | tuple[str, str]] = []
        rest = tokens[i:]
        ImportParser._collect_imports(rest, [], names)

        return IRImport(
            pos=tokens[0].pos,
            modules=modules,
            names=names,
            is_from=True,
            level=level,
        )
