from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dt import PyLine, Token

kwords = frozenset(
    {
        "and",
        "as",
        "assert",
        "async",  # forbitten
        "await",
        "break",
        "case",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "False",
        "finally",
        "for",
        "from",
        "global",  # forbitten
        "if",
        "import",
        "in",
        "is",
        "lambda",  # forbitten
        "match",
        "None",
        "nonlocal",  # forbitten
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "True",
        "try",
        "while",
        "with",
        "yield",  # forbitten
    }
)


@dataclass
class _RawLine:
    intend: int
    raw_strs: list[str]
    line_num: int


class PyRead:
    @classmethod
    def read_file_to_tokens(cls, path: Path) -> list[Any]:  # type: ignore
        text = path.read_text("utf-8-sig")  # fuckoff utf-8 bom
        compile(text, path.name, "exec")
        raw = cls._to_raw_text(text)

        lines = cls._to_raw_lines(raw)

        # TODO: У нас есть теперь RawLine. Можем начать парсить внутренние raw_strs в Token

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
                parts.extend(stripped.split())

            if parts:
                output.append(parts)

        return output

    @classmethod
    def _to_raw_lines(cls, lines: list[list[str]]) -> list[_RawLine]:
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

                    # По факту это гвард для неверных отступов. Но я не думаю что
                    # compile() допустит этого, так что похуй
                    # if not indent_stack or indent_stack[-1] != n_off:
                    #    pass

                tokens = line[1:]

            else:
                tokens = line

            output.append(_RawLine(current_level, tokens, line_number))

        return output


PyRead.read_file_to_tokens(Path(r"F:\Desktop\plg\plg-reader\plg-reader\_py_r.py"))
