from __future__ import annotations

from pathlib import Path

from .dat_cl import MULTI_CHAR_OPS, SEPARATORS, RawLine


class RawLineBuilder:
    """
    Лексер Python-файлов с построчным представлением.

    Особенности:
      - строки (одинарные/двойные) извлекаются целиком с кавычками
      - тройные кавычки обрабатываются построчно: открывающие/закрывающие как отдельные токены
      - f/r префиксы отделяются от строк
      - комментарии от '#' до конца строки – один токен
      - физические строки с '\\' склеиваются
      - пустые строки сохраняются с пустым списком токенов
      - отступы вычисляются как количество начальных пробелов/табуляций (таб = 1)
    """

    @classmethod
    def read_file_to_raw_lines(
        cls,
        path: Path,
        strip_comments: bool = False,
    ) -> list[RawLine]:
        text = path.read_text("utf-8-sig")  # fuckoff utf-8 bom
        compile(text, path.name, "exec")  # simple safeguard
        logical_lines = cls._join_continued_lines(text.splitlines())
        raw_lines, _ = cls._process_lines_with_multiline_state(
            logical_lines, strip_comments
        )
        return cls._assign_indent_levels(raw_lines)

    @staticmethod
    def _join_continued_lines(physical_lines: list[str]) -> list[str]:
        logical = []
        current = []
        for line in physical_lines:
            if line.endswith("\\"):
                current.append(line[:-1])

            else:
                current.append(line)
                logical.append("".join(current))
                current = []

        if current:
            logical.append("".join(current))

        return logical

    @classmethod
    def _process_lines_with_multiline_state(
        cls,
        logical_lines: list[str],
        strip_comments: bool,
    ) -> tuple[list[RawLine], tuple[str, int] | None]:
        """
        Возвращает список RawLine и состояние незакрытой многострочной строки.
        Состояние: (тип кавычки, текущий отступ для следующих строк) или None.
        """
        raw_lines = []
        in_multiline: tuple[str, int] | None = None

        for line_num, line in enumerate(logical_lines, start=1):
            stripped = line.lstrip(" \t")
            indent_len = len(line) - len(stripped)

            if in_multiline is not None:
                quote_type, _ = in_multiline
                end_idx = line.find(quote_type)
                if end_idx != -1:
                    content = line[:end_idx]
                    tokens = []
                    if content and not content.isspace():
                        tokens.append(content)

                    tokens.append(quote_type)
                    rest = line[end_idx + len(quote_type) :]
                    rest_tokens, new_multiline = (
                        cls._tokenize_line_with_multiline_start(rest, strip_comments)
                    )
                    tokens.extend(rest_tokens)
                    raw_lines.append(
                        RawLine(
                            indent=indent_len,
                            abs_indent=indent_len,
                            raw_strs=tokens,
                            line_num=line_num,
                            is_string_content=False,
                        )
                    )
                    in_multiline = new_multiline

                else:
                    raw_lines.append(
                        RawLine(
                            indent=indent_len,
                            abs_indent=indent_len,
                            raw_strs=[line],
                            line_num=line_num,
                            is_string_content=True,
                        )
                    )
                continue

            tokens, new_multiline = cls._tokenize_line_with_multiline_start(
                stripped, strip_comments
            )
            raw_lines.append(
                RawLine(
                    indent=indent_len,
                    abs_indent=indent_len,
                    raw_strs=tokens,
                    line_num=line_num,
                    is_string_content=False,
                )
            )
            if new_multiline is not None:
                quote_type, _ = new_multiline
                in_multiline = (quote_type, indent_len)

        return raw_lines, in_multiline

    @classmethod
    def _tokenize_line_with_multiline_start(
        cls, line: str, strip_comments: bool
    ) -> tuple[list[str], tuple[str, int] | None]:
        """
        Токенизирует строку, не находящуюся внутри многострочной строки.
        Возвращает (токены, состояние_незакрытой_тройной_строки или None).
        """
        tokens = []
        i = 0
        n = len(line)

        while i < n:
            ch = line[i]

            if ch.isspace():
                i += 1
                continue

            if ch == "#":
                if not strip_comments:
                    tokens.append(line[i:])

                break

            prefix = ""
            j = i
            while j < n and line[j].lower() in "furb":
                j += 1

            if j > i and j < n and line[j] in "\"'":
                prefix = line[i:j]
                i = j
                ch = line[i]

            if ch in "\"'":
                is_triple = i + 2 < n and line[i : i + 3] == ch * 3
                quote_token = ch * 3 if is_triple else ch

                if prefix:
                    tokens.append(prefix)

                tokens.append(quote_token)

                if is_triple:
                    i += 3
                    remaining = line[i:]
                    end_idx = remaining.find(quote_token)
                    if end_idx == -1:
                        if remaining:
                            tokens.append(remaining)

                        return tokens, (quote_token, 0)

                    else:
                        content = remaining[:end_idx]
                        if content:
                            tokens.append(content)

                        tokens.append(quote_token)
                        i += end_idx + 3
                        continue

                else:
                    i += 1
                    start = i
                    escape = False
                    while i < n:
                        c = line[i]
                        if escape:
                            escape = False
                            i += 1
                            continue

                        if c == "\\":
                            escape = True
                            i += 1
                            continue

                        if c == ch:
                            break

                        i += 1

                    i += 1
                    string_token = line[start - 1 : i]
                    tokens.pop()
                    if prefix:
                        tokens.pop()
                        tokens.append(prefix)

                    tokens.append(string_token)
                    continue

            if i + 1 < n:
                two = line[i : i + 2]
                if two in MULTI_CHAR_OPS:
                    tokens.append(two)
                    i += 2
                    continue
                if i + 2 < n and line[i : i + 3] == "...":
                    tokens.append("...")
                    i += 3
                    continue

            if ch in SEPARATORS:
                tokens.append(ch)
                i += 1
                continue

            start = i
            while i < n and not line[i].isspace() and line[i] not in SEPARATORS:
                if i + 1 < n and line[i : i + 2] in MULTI_CHAR_OPS:
                    break
                i += 1

            tokens.append(line[start:i])

        return tokens, None

    @staticmethod
    def _assign_indent_levels(raw_lines: list[RawLine]) -> list[RawLine]:
        """
        Преобразует абсолютные отступы (количество пробелов/табов) в уровни вложенности.
        Строки, помеченные is_string_content=True, не влияют на стек отступов.
        После обработки:
          - `indent` - логический уровень вложенности (0, 1, 2, ...)
          - `abs_indent` - исходное количество символов отступа в строке
        """
        output = []
        indent_stack = [0]
        current_level = 0

        for line in raw_lines:
            if line.is_string_content:
                output.append(
                    RawLine(
                        indent=current_level,
                        abs_indent=line.abs_indent,
                        raw_strs=line.raw_strs,
                        line_num=line.line_num,
                        is_string_content=True,
                    )
                )
                continue

            indent = line.abs_indent
            if indent > indent_stack[-1]:
                indent_stack.append(indent)
                current_level += 1

            elif indent < indent_stack[-1]:
                while indent_stack and indent_stack[-1] > indent:
                    indent_stack.pop()
                    current_level -= 1

            output.append(
                RawLine(
                    indent=current_level,
                    abs_indent=line.abs_indent,
                    raw_strs=line.raw_strs,
                    line_num=line.line_num,
                    is_string_content=False,
                )
            )

        return output
