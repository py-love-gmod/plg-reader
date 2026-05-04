from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .dt import (
    KWORD,
    KWORD_BAN,
    MULTI_CHAR_OPS,
    SEPARATORS,
    Line,
    MultilineState,
    Token,
    TokenType,
)


# маппинг логической колонки -> физическая позиция
class LineSegment:
    __slots__ = ("offset", "phys_line", "phys_col_start", "length")

    def __init__(self, offset: int, phys_line: int, phys_col_start: int, length: int):
        self.offset = offset
        self.phys_line = phys_line
        self.phys_col_start = phys_col_start
        self.length = length

    def physical_pos(self, logical_col: int) -> tuple[int, int]:
        if not (self.offset <= logical_col < self.offset + self.length):
            raise ValueError("logical_col вне сегмента")

        delta = logical_col - self.offset
        return self.phys_line, self.phys_col_start + delta


def build_physical_mapper(
    segments: list[LineSegment],
) -> Callable[[int], tuple[int, int]]:
    def mapper(logical_col: int) -> tuple[int, int]:
        for seg in segments:
            if seg.offset <= logical_col < seg.offset + seg.length:
                return seg.physical_pos(logical_col)

        return segments[0].phys_line, 0

    return mapper


class FileParser:
    @classmethod
    def parse(cls, file_path: Path, strip_comments: bool = False) -> list[Line]:
        text = file_path.read_text("utf-8-sig")
        compile(text, file_path.name, "exec")
        logical_lines = cls._join_continued_lines(text)
        lines_with_tokens = cls._scan_logical_lines(logical_lines, strip_comments)
        return cls._assign_indents(lines_with_tokens)

    # Склеивание строк с \
    @staticmethod
    def _join_continued_lines(text: str) -> list[tuple[str, list[LineSegment]]]:
        physical = text.splitlines(keepends=False)
        logical = []
        current_parts = []
        line_num = 1

        for raw_line in physical:
            if raw_line.endswith("\\"):
                part = raw_line[:-1]
                if current_parts:
                    stripped = part.lstrip(" \t")
                    removed = len(part) - len(stripped)
                    current_parts.append((stripped, line_num, removed, len(stripped)))

                else:
                    current_parts.append((part, line_num, 0, len(part)))

            else:
                if current_parts:
                    stripped = raw_line.lstrip(" \t")
                    removed = len(raw_line) - len(stripped)
                    current_parts.append((stripped, line_num, removed, len(stripped)))

                else:
                    current_parts.append((raw_line, line_num, 0, len(raw_line)))

                full_text = ""
                segments = []
                for pt, ln, col_start, length in current_parts:
                    offset = len(full_text)
                    full_text += pt
                    segments.append(LineSegment(offset, ln, col_start, length))

                logical.append((full_text, segments))
                current_parts.clear()

            line_num += 1

        if current_parts:
            full_text = ""
            segments = []
            for pt, ln, col_start, length in current_parts:
                offset = len(full_text)
                full_text += pt
                segments.append(LineSegment(offset, ln, col_start, length))

            logical.append((full_text, segments))

        return logical

    # Разбор логических строк, учёт multiline-состояний
    @classmethod
    def _scan_logical_lines(
        cls,
        logical: list[tuple[str, list[LineSegment]]],
        strip_comments: bool,
    ) -> list[tuple[list[Token], int, int]]:
        result = []
        state: MultilineState | None = None

        for text, segments in logical:
            first_line = segments[0].phys_line
            indent_spaces = len(text) - len(text.lstrip(" \t"))

            if state is not None:
                token_groups, new_state = cls._continue_multiline(
                    text, segments, state, strip_comments
                )
                state = new_state
                if not token_groups and state is None:
                    result.append(([], first_line, indent_spaces))

                else:
                    for tokens in token_groups:
                        if tokens or state is None:
                            result.append((tokens, first_line, indent_spaces))

                continue

            token_groups, new_state = cls._scan_line(
                text, indent_spaces, segments, strip_comments
            )
            state = new_state
            if not token_groups and state is None:
                result.append(([], first_line, indent_spaces))

            else:
                for tokens in token_groups:
                    if tokens or state is None:
                        result.append((tokens, first_line, indent_spaces))

        return result

    @classmethod
    def _scan_line(
        cls,
        text: str,
        indent_spaces: int,
        segments: list[LineSegment],
        strip_comments: bool,
    ) -> tuple[list[list[Token]], MultilineState | None]:
        to_phys = build_physical_mapper(segments)
        tokens = []
        pos = indent_spaces
        i = indent_spaces
        n = len(text)

        while i < n:
            ch = text[i]
            if ch.isspace():
                i += 1
                pos += 1
                continue

            start_col = pos

            if ch == "#":
                if not strip_comments:
                    tokens.append(
                        Token(to_phys(start_col), text[i:], TokenType.COMMENT)
                    )

                break

            # строки
            if ch in "\"'":
                token, new_i, new_state = cls._read_string(text, i, start_col, to_phys)
                if new_state is not None:
                    new_state.tokens_before = tokens
                    return [], new_state

                if token is not None:
                    tokens.append(token)

                i = new_i
                pos = start_col + (new_i - i)
                continue

            # строки с префиксами
            j = i
            while j < n and text[j].lower() in "furb":
                j += 1

            if j > i and j < n and text[j] in "\"'":
                token, new_i, new_state = cls._read_string(text, i, start_col, to_phys)
                if new_state is not None:
                    new_state.tokens_before = tokens
                    return [], new_state

                if token is not None:
                    tokens.append(token)

                i = new_i
                pos = start_col + (new_i - i)
                continue

            # многосимвольные операторы
            if i + 1 < n and text[i : i + 2] in MULTI_CHAR_OPS:
                tokens.append(
                    Token(
                        to_phys(start_col),
                        text[i : i + 2],
                        TokenType.OP,
                        subtype=text[i : i + 2],
                    )
                )
                i += 2
                pos += 2
                continue

            if i + 2 < n and text[i : i + 3] == "...":
                tokens.append(
                    Token(to_phys(start_col), "...", TokenType.OP, subtype="...")
                )
                i += 3
                pos += 3
                continue

            # разделители
            if ch in SEPARATORS:
                ttype, subtype = cls._classify_separator(ch)
                tokens.append(Token(to_phys(start_col), ch, ttype, subtype))
                i += 1
                pos += 1
                continue

            # числа (и то, что похоже на число)
            if ch.isdigit() or (ch == "." and i + 1 < n and text[i + 1].isdigit()):
                j = i
                while j < n and (
                    text[j].isdigit()
                    or text[j] == "."
                    or text[j] in "eE"
                    or (text[j] in "+-" and j > i and text[j - 1] in "eE")
                    or (text[j] in "jJ" and j == n - 1)
                    or text[j] == "_"
                ):
                    j += 1

                if j < n and text[j].isalpha() and text[j] not in "eEjJ":
                    j = i
                    while j < n and not text[j].isspace() and text[j] not in SEPARATORS:
                        if j + 1 < n and text[j : j + 2] in MULTI_CHAR_OPS:
                            break

                        j += 1

                    token_text = text[i:j]
                    token = cls._create_name_or_number_token(
                        token_text, to_phys(start_col)
                    )

                else:
                    token_text = text[i:j]
                    token = cls._create_number_token(token_text, to_phys(start_col))

                tokens.append(token)
                i = j
                pos = start_col + len(token_text)
                continue

            # имена / ключевые слова
            j = i
            while j < n and not text[j].isspace() and text[j] not in SEPARATORS:
                if j + 1 < n and text[j : j + 2] in MULTI_CHAR_OPS:
                    break

                j += 1

            token_text = text[i:j]
            token = cls._create_name_or_number_token(token_text, to_phys(start_col))
            tokens.append(token)
            i = j
            pos = start_col + len(token_text)

        return cls._split_on_semicolon(tokens), None

    @classmethod
    def _continue_multiline(
        cls,
        text: str,
        segments: list[LineSegment],
        state: MultilineState,
        strip_comments: bool,
    ) -> tuple[list[list[Token]], MultilineState | None]:
        quote = state.quote
        end_idx = text.find(quote)
        if end_idx == -1:
            state.parts.append(text + "\n")
            return [], state

        content_before = text[:end_idx]
        state.parts.append(content_before)

        full_data = state.prefix + state.quote + "".join(state.parts) + state.quote
        token = Token(pos=state.start_pos, data=full_data, type=TokenType.MULT_STRING)

        remaining_text = text[end_idx + len(quote) :]
        remaining_groups = []
        new_state = None
        if remaining_text:
            remaining_groups, new_state = cls._scan_line(
                remaining_text, 0, segments, strip_comments
            )

        all_tokens = state.tokens_before + [token]
        if remaining_groups:
            result = [all_tokens, *remaining_groups]

        else:
            result = [all_tokens]

        return result, new_state

    @classmethod
    def _read_string(
        cls,
        text: str,
        i: int,
        start_col: int,
        to_phys: Callable[[int], tuple[int, int]],
    ) -> tuple[Token | None, int, MultilineState | None]:
        n = len(text)
        prefix = ""
        while i < n and text[i].lower() in "furb":
            prefix += text[i]
            i += 1

        quote_char = text[i]
        is_triple = i + 2 < n and text[i : i + 3] == quote_char * 3
        quote_len = 3 if is_triple else 1
        quote_token = quote_char * quote_len
        i += quote_len

        if is_triple:
            j = i
            while j < n:
                if text[j : j + 3] == quote_token:
                    break

                j += 1

            if j < n:
                content = text[i:j]
                full_str = prefix + quote_token + content + quote_token
                token = Token(to_phys(start_col), full_str, TokenType.MULT_STRING)
                return token, j + 3, None

            else:
                content = text[i:]
                state = MultilineState(
                    prefix=prefix,
                    quote=quote_token,
                    parts=[content + "\n"],
                    start_pos=to_phys(start_col),
                    tokens_before=[],
                )
                return None, i, state

        else:
            j = i
            escape = False
            while j < n:
                c = text[j]
                if escape:
                    escape = False
                    j += 1
                    continue

                if c == "\\":
                    escape = True
                    j += 1
                    continue

                if c == quote_char:
                    break

                j += 1

            full_str = prefix + quote_char + text[i:j] + quote_char
            token = Token(to_phys(start_col), full_str, TokenType.STRING)
            return token, j + 1, None

    # Утилиты
    @staticmethod
    def _classify_separator(ch: str) -> tuple[TokenType, str | None]:
        if ch in "([{":
            return TokenType.PARENTHESE_OPEN, None

        if ch in ")]}":
            return TokenType.PARENTHESE_CLOSE, None

        if ch == ",":
            return TokenType.COMMA, None

        if ch == ".":
            return TokenType.DOT, None

        return TokenType.OP, ch

    @staticmethod
    def _create_number_token(text: str, pos: tuple[int, int]) -> Token:
        s_clean = text.replace("_", "")
        if s_clean.endswith(("j", "J")):
            raise RuntimeError(
                f"Комплексные числа не разрешены: '{text}' на строке {pos[0]}, позиция {pos[1]}"
            )

        try:
            value = int(s_clean, 0)

        except ValueError:
            value = float(s_clean)

        return Token(pos, value, TokenType.NUMBER)

    @staticmethod
    def _is_number(s: str) -> bool:
        s_clean = s.replace("_", "")
        if s_clean.endswith(("j", "J")):
            return False

        if re.match(r"^0[xX][0-9a-fA-F]+$", s_clean):
            return True

        if re.match(r"^0[bB][01]+$", s_clean):
            return True

        if re.match(r"^0[oO][0-7]+$", s_clean):
            return True

        try:
            float(s_clean)
            return True

        except ValueError:
            return False

    @staticmethod
    def _create_name_or_number_token(text: str, pos: tuple[int, int]) -> Token:
        if text in KWORD:
            return Token(pos, text, TokenType.KWORD)

        if text in KWORD_BAN:
            raise RuntimeError(
                f"Запрещённое ключевое слово '{text}' на строке {pos[0]}, позиция {pos[1]}"
            )

        if FileParser._is_number(text):
            s_clean = text.replace("_", "")
            try:
                value = int(s_clean, 0)

            except ValueError:
                value = float(s_clean)

            return Token(pos, value, TokenType.NUMBER)

        return Token(pos, text, TokenType.NAME)
    @staticmethod
    def _split_on_semicolon(tokens: list[Token]) -> list[list[Token]]:
        groups = []
        current = []
        for t in tokens:
            if t.type == TokenType.OP and t.data == ";":
                if current:
                    groups.append(current)
                    current = []
        
            else:
                current.append(t)
        
        if current:
            groups.append(current)
        
        return groups

    # Определение отступов
    @classmethod
    def _assign_indents(
        cls, lines_info: list[tuple[list[Token], int, int]]
    ) -> list[Line]:
        output = []
        indent_stack = [0]
        current_indent = 0

        for tokens, line_num, indent_spaces in lines_info:
            if not tokens or all(t.type == TokenType.COMMENT for t in tokens):
                output.append(Line(current_indent, line_num, tokens))
                continue

            if indent_spaces > indent_stack[-1]:
                indent_stack.append(indent_spaces)
                current_indent += 1

            elif indent_spaces < indent_stack[-1]:
                while indent_stack and indent_stack[-1] > indent_spaces:
                    indent_stack.pop()
                    current_indent -= 1

            output.append(Line(current_indent, line_num, tokens))

        return output
