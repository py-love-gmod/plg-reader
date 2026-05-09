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
    Token,
    TokenType,
)


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


class _StringContinuation:
    __slots__ = (
        "prefix",
        "quote",
        "is_fstring",
        "accumulated",
        "pending_str",
        "start_pos",
        "tokens_before",
    )

    def __init__(
        self,
        prefix: str,
        quote: str,
        start_pos: tuple[int, int],
        is_fstring: bool,
        tokens_before: list[Token],
    ):
        self.prefix = prefix
        self.quote = quote
        self.is_fstring = is_fstring
        self.accumulated: list = []
        self.pending_str: str = ""
        self.start_pos = start_pos
        self.tokens_before = tokens_before


class FileParser:
    _RE_HEX = re.compile(r"^0[xX][0-9a-fA-F]+$")
    _RE_BIN = re.compile(r"^0[bB][01]+$")
    _RE_OCT = re.compile(r"^0[oO][0-7]+$")

    @classmethod
    def parse(cls, file_path: Path, strip_comments: bool = False) -> list[Line]:
        text = file_path.read_text("utf-8-sig")
        compile(text, file_path.name, "exec")
        logical_lines = cls._join_continued_lines(text)
        lines_with_tokens = cls._scan_logical_lines(logical_lines, strip_comments)
        return cls._assign_indents(lines_with_tokens)

    @staticmethod
    def _find_continuation_boundary(line: str) -> tuple[int, bool]:
        n = len(line)
        in_string = False
        string_char = ""
        triple = False
        escape = False
        comment_start = n

        i = 0
        while i < n:
            ch = line[i]
            if not in_string:
                if ch == "#":
                    comment_start = i
                    break

                elif ch in "\"'":
                    in_string = True
                    string_char = ch
                    triple = i + 2 < n and line[i : i + 3] == ch * 3
                    if triple:
                        i += 3
                        continue

            else:
                if escape:
                    escape = False
                    i += 1
                    continue

                if triple:
                    if line[i : i + 3] == string_char * 3:
                        in_string = False
                        triple = False
                        i += 3
                        continue

                else:
                    if ch == "\\":
                        escape = True
                        i += 1
                        continue

                    if ch == string_char:
                        in_string = False

            i += 1

        code_part = line[:comment_start].rstrip(" \t")
        if not code_part:
            return 0, False

        if code_part[-1] == "\\":
            last_slash = line.rfind("\\", 0, comment_start)
            after_slash = line[last_slash + 1 : comment_start]
            if not after_slash or after_slash.isspace():
                return last_slash, True

        return 0, False

    @staticmethod
    def _join_continued_lines(text: str) -> list[tuple[str, list[LineSegment]]]:
        physical = text.splitlines(keepends=False)
        logical: list[tuple[str, list[LineSegment]]] = []
        current_parts: list[tuple[str, int, int, int]] = []
        line_num = 1

        for raw_line in physical:
            end_code_idx, is_continuation = FileParser._find_continuation_boundary(
                raw_line
            )
            if is_continuation:
                part = raw_line[:end_code_idx]
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
                segments: list[LineSegment] = []
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

    @classmethod
    def _scan_logical_lines(
        cls,
        logical: list[tuple[str, list[LineSegment]]],
        strip_comments: bool,
    ) -> list[tuple[list[Token], int, int]]:
        result: list[tuple[list[Token], int, int]] = []
        pending: _StringContinuation | None = None

        for text, segments in logical:
            first_line = segments[0].phys_line
            indent_spaces = len(text) - len(text.lstrip(" \t"))

            if pending is not None:
                new_tokens, pending = cls._continue_string(text, segments, pending)
                for tokens in new_tokens:
                    result.append((tokens, first_line, indent_spaces))

                continue

            token_groups, pending = cls._scan_line(
                text, indent_spaces, segments, strip_comments
            )
            if not token_groups and pending is None:
                result.append(([], first_line, indent_spaces))

            else:
                for tokens in token_groups:
                    result.append((tokens, first_line, indent_spaces))

        return result

    @classmethod
    def _scan_line(
        cls,
        text: str,
        indent_spaces: int,
        segments: list[LineSegment],
        strip_comments: bool,
    ) -> tuple[list[list[Token]], _StringContinuation | None]:
        to_phys = build_physical_mapper(segments)
        tokens: list[Token] = []
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

            j = i
            while j < n and text[j].lower() in "furb":
                j += 1

            if j < n and text[j] in "\"'":
                prefix = text[i:j].lower()
                is_f = "f" in prefix
                if is_f:
                    token, new_i, pending = cls._read_fstring(
                        text, i, start_col, to_phys, tokens
                    )

                else:
                    token, new_i, pending = cls._read_simple_string(
                        text, i, start_col, to_phys, tokens
                    )

                if pending is not None:
                    return cls._split_on_semicolon(tokens), pending

                if token is not None:
                    tokens.append(token)

                i = new_i
                pos = start_col + (new_i - i)
                continue

            if (
                ch in "+-"
                and i + 1 < n
                and (text[i + 1].isdigit() or text[i + 1] == ".")
            ):
                prev = tokens[-1] if tokens else None
                unary_ok = prev is None or prev.type in (
                    TokenType.OP,
                    TokenType.PARENTHESE_OPEN,
                    TokenType.COMMA,
                    TokenType.KWORD,
                    TokenType.PARENTHESE_CLOSE,
                    TokenType.DOT,
                )
                if unary_ok:
                    i += 1
                    pos += 1
                    num_str, new_i = cls._read_number(text, i)
                    i = new_i
                    token_text = ch + num_str
                    token = cls._create_number_token(token_text, to_phys(start_col))
                    tokens.append(token)
                    pos = start_col + len(token_text)
                    continue

            if i + 1 < n and text[i : i + 2] in MULTI_CHAR_OPS:
                tokens.append(Token(to_phys(start_col), text[i : i + 2], TokenType.OP))
                i += 2
                pos += 2
                continue

            if i + 2 < n and text[i : i + 3] == "...":
                tokens.append(Token(to_phys(start_col), "...", TokenType.OP))
                i += 3
                pos += 3
                continue

            if ch in SEPARATORS:
                ttype = cls._classify_separator(ch)
                tokens.append(Token(to_phys(start_col), ch, ttype))
                i += 1
                pos += 1
                continue

            if ch.isdigit() or (ch == "." and i + 1 < n and text[i + 1].isdigit()):
                num_str, j = cls._read_number(text, i)
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
                    token_text = num_str
                    token = cls._create_number_token(token_text, to_phys(start_col))

                tokens.append(token)
                i = j
                pos = start_col + len(token_text)
                continue

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
    def _read_simple_string(
        cls,
        text: str,
        i: int,
        start_col: int,
        to_phys: Callable,
        tokens_before: list[Token],
    ) -> tuple[Token | None, int, _StringContinuation | None]:
        n = len(text)
        prefix = ""
        while i < n and text[i].lower() in "furb":
            prefix += text[i]
            i += 1

        quote_char = text[i]
        is_triple = i + 2 < n and text[i : i + 3] == quote_char * 3
        quote = quote_char * 3 if is_triple else quote_char
        i += len(quote)

        if is_triple:
            j = i
            while j < n:
                if text[j : j + 3] == quote:
                    break

                j += 1

            if j < n:
                content = text[i:j]
                token = Token(
                    pos=to_phys(start_col),
                    data=(prefix, quote + content + quote),
                    type=TokenType.STRING,
                )
                return token, j + 3, None

            else:
                state = _StringContinuation(
                    prefix=prefix,
                    quote=quote,
                    start_pos=to_phys(start_col),
                    is_fstring=False,
                    tokens_before=tokens_before,
                )
                state.accumulated = [text[i:] + "\n"]
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

            token = Token(
                pos=to_phys(start_col),
                data=(prefix, quote_char + text[i:j] + quote_char),
                type=TokenType.STRING,
            )
            return token, j + 1, None

    @classmethod
    def _read_fstring(
        cls,
        text: str,
        i: int,
        start_col: int,
        to_phys: Callable,
        tokens_before: list[Token],
    ) -> tuple[Token | None, int, _StringContinuation | None]:
        n = len(text)
        prefix = ""
        while i < n and text[i].lower() in "furb":
            prefix += text[i]
            i += 1

        quote_char = text[i]
        is_triple = i + 2 < n and text[i : i + 3] == quote_char * 3
        quote = quote_char * 3 if is_triple else quote_char
        i += len(quote)

        accumulated, pending_str, found_end, new_i = cls._parse_fstring_parts(
            text, i, quote, to_phys, [], ""
        )

        if found_end:
            if pending_str:
                accumulated.append(pending_str)

            token = Token(
                pos=to_phys(start_col),
                data=(prefix, accumulated),
                type=TokenType.FORMATTED_STRING,
            )
            return token, new_i, None

        else:
            state = _StringContinuation(
                prefix=prefix,
                quote=quote,
                start_pos=to_phys(start_col),
                is_fstring=True,
                tokens_before=tokens_before,
            )
            state.accumulated = accumulated
            state.pending_str = pending_str + "\n"
            return None, new_i, state

    @classmethod
    def _parse_fstring_parts(
        cls,
        text: str,
        start: int,
        quote: str,
        to_phys: Callable,
        accumulated: list,
        pending_str: str,
    ) -> tuple[list, str, bool, int]:
        n = len(text)
        i = start
        cur_literal = pending_str

        while i < n:
            if text[i : i + len(quote)] == quote:
                return accumulated, cur_literal, True, i + len(quote)

            if text[i] == "{":
                if i + 1 < n and text[i + 1] == "{":
                    cur_literal += "{"
                    i += 2
                    continue

                if cur_literal:
                    accumulated.append(cur_literal)
                    cur_literal = ""

                i += 1
                expr_tokens, new_i = cls._parse_f_expression(text, i, to_phys)
                accumulated.append(expr_tokens)
                i = new_i
                continue

            if text[i] == "}":
                if i + 1 < n and text[i + 1] == "}":
                    cur_literal += "}"
                    i += 2
                    continue

                cur_literal += "}"
                i += 1
                continue

            cur_literal += text[i]
            i += 1

        return accumulated, cur_literal, False, i

    @classmethod
    def _parse_f_expression(
        cls,
        text: str,
        i: int,
        to_phys: Callable,
    ) -> tuple[list[Token], int]:
        depth = 1
        j = i
        in_string = False
        string_char = ""
        while j < len(text) and depth > 0:
            c = text[j]
            if in_string:
                if c == "\\":
                    j += 1

                elif c == string_char:
                    in_string = False

            else:
                if c in "\"'":
                    in_string = True
                    string_char = c

                elif c == "{":
                    depth += 1

                elif c == "}":
                    depth -= 1

            j += 1

        if depth != 0:
            raise SyntaxError("f-string: mismatched '{' in expression")

        expr_text = text[i : j - 1]

        def inner_to_phys(local_col):
            return to_phys(i + local_col)

        tokens = cls._tokenize_expression(expr_text, inner_to_phys)
        return tokens, j

    @classmethod
    def _tokenize_expression(
        cls,
        expr: str,
        to_phys: Callable,
    ) -> list[Token]:
        tokens = []
        i = 0
        n = len(expr)
        while i < n:
            ch = expr[i]
            if ch.isspace():
                i += 1
                continue

            start_col = i
            if ch in "\"'":
                token, new_i = cls._read_simple_string_expression(
                    expr, i, start_col, to_phys
                )
                tokens.append(token)
                i = new_i
                continue

            if (
                ch in "+-"
                and i + 1 < n
                and (expr[i + 1].isdigit() or expr[i + 1] == ".")
            ):
                prev = tokens[-1] if tokens else None
                unary_ok = prev is None or prev.type in (
                    TokenType.OP,
                    TokenType.PARENTHESE_OPEN,
                    TokenType.COMMA,
                    TokenType.KWORD,
                    TokenType.PARENTHESE_CLOSE,
                    TokenType.DOT,
                )
                if unary_ok:
                    i += 1
                    num_str, new_i = cls._read_number(expr, i)
                    i = new_i
                    token_text = ch + num_str
                    token = cls._create_number_token(token_text, to_phys(start_col))
                    tokens.append(token)
                    continue

            if i + 1 < n and expr[i : i + 2] in MULTI_CHAR_OPS:
                tokens.append(Token(to_phys(start_col), expr[i : i + 2], TokenType.OP))
                i += 2
                continue

            if i + 2 < n and expr[i : i + 3] == "...":
                tokens.append(Token(to_phys(start_col), "...", TokenType.OP))
                i += 3
                continue

            if ch in SEPARATORS:
                ttype = cls._classify_separator(ch)
                tokens.append(Token(to_phys(start_col), ch, ttype))
                i += 1
                continue

            if ch.isdigit() or (ch == "." and i + 1 < n and expr[i + 1].isdigit()):
                num_str, j = cls._read_number(expr, i)
                if j < n and expr[j].isalpha() and expr[j] not in "eEjJ":
                    j = i
                    while j < n and not expr[j].isspace() and expr[j] not in SEPARATORS:
                        if j + 1 < n and expr[j : j + 2] in MULTI_CHAR_OPS:
                            break

                        j += 1

                    token_text = expr[i:j]
                    token = cls._create_name_or_number_token(
                        token_text, to_phys(start_col)
                    )

                else:
                    token_text = num_str
                    token = cls._create_number_token(token_text, to_phys(start_col))

                tokens.append(token)
                i = j
                continue

            j = i
            while j < n and not expr[j].isspace() and expr[j] not in SEPARATORS:
                if j + 1 < n and expr[j : j + 2] in MULTI_CHAR_OPS:
                    break

                j += 1

            token_text = expr[i:j]
            token = cls._create_name_or_number_token(token_text, to_phys(start_col))
            tokens.append(token)
            i = j

        return tokens

    @classmethod
    def _read_simple_string_expression(cls, text, i, start_col, to_phys):
        quote = text[i]
        i += 1
        n = len(text)
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

            if c == quote:
                break

            j += 1

        content = text[i:j]
        token = Token(to_phys(start_col), quote + content + quote, TokenType.STRING)
        return token, j + 1

    @classmethod
    def _continue_string(
        cls,
        text: str,
        segments: list[LineSegment],
        state: _StringContinuation,
    ) -> tuple[list[list[Token]], _StringContinuation | None]:
        to_phys = build_physical_mapper(segments)

        if state.is_fstring:
            state.pending_str += text + "\n"
            accumulated, pending_str, found_end, end_i = cls._parse_fstring_parts(
                text, 0, state.quote, to_phys, state.accumulated, state.pending_str
            )
            if found_end:
                if pending_str:
                    accumulated.append(pending_str)

                token = Token(
                    pos=state.start_pos,
                    data=(state.prefix, accumulated),
                    type=TokenType.FORMATTED_STRING,
                )
                remaining = text[end_i:]
                if remaining.strip():
                    result_groups, _ = cls._scan_line(
                        remaining, 0, segments, strip_comments=False
                    )
                    return [state.tokens_before + [token]] + result_groups, None

                else:
                    return [state.tokens_before + [token]], None

            else:
                state.accumulated = accumulated
                state.pending_str = pending_str
                return [], state

        else:
            state.accumulated.append(text + "\n")
            quote = state.quote
            idx = text.find(quote)
            if idx == -1:
                return [], state

            before = text[:idx]
            parts = state.accumulated[:-1] + [before]
            full_content = "".join(parts)
            token = Token(
                pos=state.start_pos,
                data=(state.prefix, state.quote + full_content + state.quote),
                type=TokenType.STRING,
            )
            remaining = text[idx + len(quote) :]
            if remaining.strip():
                result_groups, _ = cls._scan_line(
                    remaining, 0, segments, strip_comments=False
                )
                return [state.tokens_before + [token]] + result_groups, None

            else:
                return [state.tokens_before + [token]], None

    @staticmethod
    def _read_number(text: str, start: int) -> tuple[str, int]:
        i = start
        n = len(text)
        while i < n and (
            text[i].isdigit()
            or text[i] == "."
            or text[i] in "eE"
            or (text[i] in "+-" and i > start and text[i - 1] in "eE")
            or (text[i] in "jJ" and i == n - 1)
            or text[i] == "_"
        ):
            i += 1

        return text[start:i], i

    @staticmethod
    def _classify_separator(ch: str) -> TokenType:
        if ch in "([{":
            return TokenType.PARENTHESE_OPEN

        if ch in ")]}":
            return TokenType.PARENTHESE_CLOSE

        if ch == ",":
            return TokenType.COMMA

        if ch == ".":
            return TokenType.DOT

        return TokenType.OP

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

    @classmethod
    def _is_number(cls, s: str) -> bool:
        s_clean = s.replace("_", "")
        if s_clean.endswith(("j", "J")):
            return False

        if cls._RE_HEX.match(s_clean):
            return True

        if cls._RE_BIN.match(s_clean):
            return True

        if cls._RE_OCT.match(s_clean):
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
        groups: list[list[Token]] = []
        current: list[Token] = []
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

    @classmethod
    def _assign_indents(
        cls, lines_info: list[tuple[list[Token], int, int]]
    ) -> list[Line]:
        output: list[Line] = []
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
