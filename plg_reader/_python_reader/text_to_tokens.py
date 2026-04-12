from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawLine:
    intend: int
    raw_strs: list[str]
    line_num: int


class PyRead:
    """
    Простейший класс для паса питоновских файлов
    """

    SEPARATORS = "()[]{},:.=+-*/%<>@\"'"
    MULTI_CHAR_OPS = {"->", "==", "!=", "<=", ">=", "//", "**"}

    @classmethod
    def read_file_to_tokens(cls, path: Path) -> list[RawLine]:
        text = path.read_text("utf-8-sig")  # fuckoff utf-8 bom
        compile(text, path.name, "exec")  # simple safeguard
        raw = cls._to_raw_text(text)
        return cls._to_raw_lines(raw)

    @classmethod
    def _split(cls, code: str) -> list[str]:
        tokens = []
        current = []
        escape = False
        i = 0
        n = len(code)

        while i < n:
            ch = code[i]

            if escape:
                if current:
                    current.append(ch)

                else:
                    current.append(ch)

                escape = False
                i += 1
                continue

            if ch == "\\":
                if current:
                    tokens.append("".join(current))
                    current = []

                escape = True
                current.append(ch)
                i += 1
                continue

            if i + 1 < n:
                two_char = code[i : i + 2]
                if two_char in cls.MULTI_CHAR_OPS:
                    if current:
                        tokens.append("".join(current))
                        current = []

                    tokens.append(two_char)
                    i += 2
                    continue

            if ch.isspace():
                if current:
                    tokens.append("".join(current))
                    current = []

                tokens.append(ch)
                i += 1
                continue

            if ch in cls.SEPARATORS:
                if current:
                    tokens.append("".join(current))
                    current = []

                tokens.append(ch)
                i += 1
                continue

            current.append(ch)
            i += 1

        if current:
            tokens.append("".join(current))

        return tokens

    @classmethod
    def _compress_tokens(cls, tokens: list[str]) -> list[str]:
        compressed = []
        i = 0
        n = len(tokens)
        while i < n:
            tok = tokens[i]
            if tok in ('"', "'"):
                j = i
                count = 0
                while j < n and tokens[j] == tok:
                    count += 1
                    j += 1

                while count >= 3:
                    compressed.append(tok * 3)
                    count -= 3

                for _ in range(count):
                    compressed.append(tok)

                i = j

            elif tok.isspace():
                i += 1

            else:
                compressed.append(tok)
                i += 1

        return compressed

    @classmethod
    def _to_raw_text(cls, strings: str) -> list[list[str]]:
        lines = strings.splitlines()
        output = []
        for line in lines:
            stripped = line.lstrip()
            indent_len = len(line) - len(stripped)

            parts = []
            if indent_len > 0:
                parts.append(f"!I:{indent_len}")

            if stripped:
                parts.extend(cls._compress_tokens(cls._split(stripped)))

            if parts:
                output.append(parts)

        return output

    @classmethod
    def _to_raw_lines(cls, lines: list[list[str]]) -> list[RawLine]:
        output = []
        line_number = 0
        indent_stack = [0]
        current_level = 0

        for line in lines:
            line_number += 1
            if line and line[0].startswith("!I:"):
                n_off = int(line[0][3:])
                if n_off > indent_stack[-1]:
                    indent_stack.append(n_off)
                    current_level += 1

                elif n_off < indent_stack[-1]:
                    while indent_stack and indent_stack[-1] > n_off:
                        indent_stack.pop()
                        current_level -= 1

                tokens = line[1:]

            else:
                tokens = line

            output.append(RawLine(current_level, tokens, line_number))

        return output
