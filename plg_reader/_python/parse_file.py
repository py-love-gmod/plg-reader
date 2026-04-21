from __future__ import annotations

import re
from pathlib import Path

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


class FileParser:
    @classmethod
    def parse(cls, file_path: Path, strip_comments: bool = False) -> list[Line]:
        text = file_path.read_text("utf-8-sig")
        compile(text, file_path.name, "exec")
        logical_lines = cls._join_continued_lines(text)
        lines_with_tokens = cls._scan_logical_lines(logical_lines, strip_comments)
        return cls._assign_indents(lines_with_tokens)

    @staticmethod
    def _join_continued_lines(text: str) -> list[tuple[str, int]]:
        physical = text.splitlines(keepends=False)
        logical = []
        current_parts = []
        start_line = 1
        line_num = 1

        for raw_line in physical:
            if raw_line.endswith("\\"):
                part = raw_line[:-1]
                if current_parts:
                    part = part.lstrip(" \t")

                current_parts.append(part)
                if len(current_parts) == 1:
                    start_line = line_num

            else:
                if current_parts:
                    raw_line = raw_line.lstrip(" \t")

                current_parts.append(raw_line)
                logical.append(("".join(current_parts), start_line))
                current_parts = []
                start_line = line_num + 1

            line_num += 1

        if current_parts:
            logical.append(("".join(current_parts), start_line))

        return logical

    @classmethod
    def _scan_logical_lines(
        cls,
        logical: list[tuple[str, int]],
        strip_comments: bool,
    ) -> list[tuple[list[Token], int, int]]:
        result = []
        state: MultilineState | None = None

        for text, line_num in logical:
            indent_spaces = len(text) - len(text.lstrip(" \t"))

            if state is not None:
                tokens, new_state = cls._continue_multiline(
                    text, line_num, state, strip_comments
                )
                state = new_state
                if tokens or state is None:
                    result.append((tokens, line_num, indent_spaces))

                continue

            tokens, new_state = cls._scan_line(
                text, indent_spaces, line_num, strip_comments
            )
            state = new_state
            if tokens or state is None:
                result.append((tokens, line_num, indent_spaces))

        return result

    @classmethod
    def _scan_line(
        cls,
        text: str,
        indent_spaces: int,
        line_num: int,
        strip_comments: bool,
    ) -> tuple[list[Token], MultilineState | None]:
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
                    tokens.append(Token(start_col, text[i:], TokenType.COMMENT))

                break

            if ch in "\"'":
                token, new_i, new_state = cls._read_string(text, i, start_col, line_num)
                if new_state is not None:
                    new_state.tokens_before = tokens
                    return [], new_state

                if token is not None:
                    tokens.append(token)

                i = new_i
                pos = start_col + (new_i - i)
                continue

            j = i
            while j < n and text[j].lower() in "furb":
                j += 1

            if j > i and j < n and text[j] in "\"'":
                token, new_i, new_state = cls._read_string(text, i, start_col, line_num)
                if new_state is not None:
                    new_state.tokens_before = tokens
                    return [], new_state

                if token is not None:
                    tokens.append(token)

                i = new_i
                pos = start_col + (new_i - i)
                continue

            if i + 1 < n and text[i : i + 2] in MULTI_CHAR_OPS:
                tokens.append(
                    Token(
                        start_col,
                        text[i : i + 2],
                        TokenType.OP,
                        subtype=text[i : i + 2],
                    )
                )
                i += 2
                pos += 2
                continue

            if i + 2 < n and text[i : i + 3] == "...":
                tokens.append(Token(start_col, "...", TokenType.OP, subtype="..."))
                i += 3
                pos += 3
                continue

            if ch in SEPARATORS:
                ttype, subtype = cls._classify_separator(ch)
                tokens.append(Token(start_col, ch, ttype, subtype))
                i += 1
                pos += 1
                continue

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
                        token_text, start_col, line_num
                    )

                else:
                    token_text = text[i:j]
                    if cls._is_number(token_text):
                        token = Token(start_col, token_text, TokenType.NUMBER)

                    else:
                        token = cls._create_name_or_number_token(
                            token_text, start_col, line_num
                        )

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
            token = cls._create_name_or_number_token(token_text, start_col, line_num)
            tokens.append(token)
            i = j
            pos = start_col + len(token_text)

        return tokens, None

    @classmethod
    def _continue_multiline(
        cls,
        text: str,
        line_num: int,
        state: MultilineState,
        strip_comments: bool,
    ) -> tuple[list[Token], MultilineState | None]:
        quote = state.quote
        end_idx = text.find(quote)
        if end_idx == -1:
            state.parts.append(text + "\n")
            return [], state

        content_before = text[:end_idx]
        state.parts.append(content_before)

        full_data = state.prefix + state.quote + "".join(state.parts) + state.quote
        token = Token(
            start=state.start_col,
            data=full_data,
            type=TokenType.MULT_STRING,
        )

        remaining_text = text[end_idx + len(quote) :]
        remaining_tokens = []
        new_state = None
        if remaining_text:
            remaining_tokens, new_state = cls._scan_line(
                remaining_text,
                0,
                line_num,
                strip_comments,
            )

        all_tokens = state.tokens_before + [token] + remaining_tokens
        return all_tokens, new_state

    @classmethod
    def _read_string(
        cls,
        text: str,
        i: int,
        start_col: int,
        line_num: int,
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
                token = Token(
                    start=start_col,
                    data=full_str,
                    type=TokenType.MULT_STRING,
                )
                return token, j + 3, None

            else:
                content = text[i:]
                state = MultilineState(
                    prefix=prefix,
                    quote=quote_token,
                    parts=[content + "\n"],
                    start_col=start_col,
                    start_line=line_num,
                    tokens_before=[],  # будет перезаписано в _scan_line
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
            token = Token(
                start=start_col,
                data=full_str,
                type=TokenType.STRING,
            )
            return token, j + 1, None

    @staticmethod
    def _classify_separator(ch: str) -> tuple[TokenType, str | None]:
        if ch in "([{":
            return TokenType.PARENTHESE_OPEN, None

        elif ch in ")]}":
            return TokenType.PARENTHESE_CLOSE, None

        elif ch == ",":
            return TokenType.COMMA, None

        elif ch == ".":
            return TokenType.DOT, None

        else:
            return TokenType.OP, ch

    @staticmethod
    def _create_name_or_number_token(text: str, start_col: int, line_num: int) -> Token:
        if text in KWORD:
            return Token(start_col, text, TokenType.KWORD)

        if text in KWORD_BAN:
            raise RuntimeError(
                f"Запрещённое ключевое слово '{text}' на строке {line_num}, позиция {start_col}"
            )

        if FileParser._is_number(text):
            return Token(start_col, text, TokenType.NUMBER)

        return Token(start_col, text, TokenType.NAME)

    @staticmethod
    def _is_number(s: str) -> bool:
        s_clean = s.replace("_", "")
        if s_clean.endswith(("j", "J")):
            s_clean = s_clean[:-1]

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
