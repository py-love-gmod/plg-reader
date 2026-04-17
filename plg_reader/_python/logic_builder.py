import re

from .dat_cl import (
    KWORD,
    KWORD_BAN,
    MULTI_CHAR_OPS,
    SEPARATORS,
    STRING_PREFIXES,
    Line,
    RawLine,
    Token,
    TokenType,
)


class LineBuilder:
    @classmethod
    def raw_lines_to_lines(cls, lines: list[RawLine]) -> list[Line]:
        output: list[Line] = []
        state: tuple[str, str, list[str], int] | None = None

        for line in lines:
            tokens, state = cls._process_line(line, state)
            if state is None or not line.is_string_content:
                output.append(Line(line.indent, line.line_num, tokens))

        return output

    @classmethod
    def _process_line(
        cls, line: RawLine, state: tuple[str, str, list[str], int] | None
    ) -> tuple[
        list[Token],
        tuple[str, str, list[str], int] | None,
    ]:
        tokens: list[Token] = []
        pos: int = line.abs_indent
        raw_strs: list[str] = line.raw_strs

        if state is not None:
            raw_strs, tokens, pos, state = cls._handle_multiline_continuation(
                line, state, tokens, pos
            )
            if state is not None:
                return tokens, state

        i: int = 0
        while i < len(raw_strs):
            raw: str = raw_strs[i]
            start_pos: int = pos
            pos += len(raw)

            if cls._is_triple_quote_start(raw, raw_strs, i):
                i, tokens, pos, new_state = cls._handle_triple_quote(
                    raw_strs, i, start_pos, pos
                )
                if new_state:
                    state = new_state
                    break

                continue

            if cls._is_string_token(raw):
                tokens.append(cls._create_string_token(raw, start_pos))
                i += 1
                continue

            if raw.startswith("#"):
                tokens.append(cls._create_token(raw, TokenType.COMMENT, start_pos))
                i += 1
                continue

            if cls._is_operator_or_separator(raw):
                tokens.append(cls._create_operator_token(raw, start_pos))
                i += 1
                continue

            if cls._is_number(raw):
                tokens.append(cls._create_token(raw, TokenType.NUMBER, start_pos))
                i += 1
                continue

            token = cls._create_name_or_keyword_token(raw, start_pos, line.line_num)
            tokens.append(token)
            i += 1

        return tokens, state

    @classmethod
    def _handle_multiline_continuation(
        cls,
        line: RawLine,
        state: tuple[str, str, list[str], int],
        tokens: list[Token],
        pos: int,
    ) -> tuple[
        list[str],
        list[Token],
        int,
        tuple[str, str, list[str], int] | None,
    ]:
        prefix, quote, parts, start_pos = state
        if line.is_string_content:
            if line.raw_strs:
                parts.append(line.raw_strs[0])
            return line.raw_strs, tokens, pos, (prefix, quote, parts, start_pos)

        try:
            quote_idx = line.raw_strs.index(quote)
        except ValueError:
            parts.extend(line.raw_strs)
            return [], tokens, pos, (prefix, quote, parts, start_pos)

        parts.extend(line.raw_strs[:quote_idx])
        full_data = prefix + quote + "".join(parts) + quote
        tokens.append(cls._create_token(full_data, TokenType.MULT_STRING, start_pos))

        remaining_raw_strs = line.raw_strs[quote_idx + 1 :]
        pos = start_pos + len(full_data)
        return remaining_raw_strs, tokens, pos, None

    @classmethod
    def _handle_triple_quote(
        cls, raw_strs: list[str], i: int, start_pos: int, pos: int
    ) -> tuple[
        int,
        list[Token],
        int,
        tuple[str, str, list[str], int] | None,
    ]:
        raw = raw_strs[i]
        if (
            raw in STRING_PREFIXES
            and i + 1 < len(raw_strs)
            and cls._is_triple_quote(raw_strs[i + 1])
        ):
            prefix = raw
            quote = raw_strs[i + 1]
            i += 2

        elif cls._is_triple_quote(raw):
            prefix = ""
            quote = raw
            i += 1

        else:
            return i, [], pos, None

        parts: list[str] = []
        while i < len(raw_strs):
            part = raw_strs[i]
            if part == quote:
                full_data = prefix + quote + "".join(parts) + quote
                token = cls._create_token(full_data, TokenType.MULT_STRING, start_pos)
                pos = start_pos + len(full_data)
                i += 1
                return i, [token], pos, None

            else:
                parts.append(part)
                i += 1

        state = (prefix, quote, parts, start_pos)
        return i, [], pos, state

    @classmethod
    def _is_triple_quote_start(cls, raw: str, raw_strs: list[str], i: int) -> bool:
        return (
            raw in STRING_PREFIXES
            and i + 1 < len(raw_strs)
            and cls._is_triple_quote(raw_strs[i + 1])
        ) or cls._is_triple_quote(raw)

    @classmethod
    def _create_string_token(cls, raw: str, start_pos: int) -> Token:
        ttype = (
            TokenType.MULT_STRING if cls._is_multiline_string(raw) else TokenType.STRING
        )
        return cls._create_token(raw, ttype, start_pos)

    @classmethod
    def _is_operator_or_separator(cls, raw: str) -> bool:
        return raw in MULTI_CHAR_OPS or (
            len(raw) == 1 and raw in SEPARATORS and not raw.isalnum()
        )

    @classmethod
    def _create_operator_token(cls, raw: str, start_pos: int) -> Token:
        if raw in "([{":
            return cls._create_token(raw, TokenType.PARENTHESE_OPEN, start_pos)

        elif raw in ")]}":
            return cls._create_token(raw, TokenType.PARENTHESE_CLOSE, start_pos)

        elif raw == ",":
            return cls._create_token(raw, TokenType.COMMA, start_pos)

        elif raw == ".":
            return cls._create_token(raw, TokenType.DOT, start_pos)

        else:
            return cls._create_token(raw, TokenType.OP, start_pos, subtype=raw)

    @classmethod
    def _create_name_or_keyword_token(
        cls,
        raw: str,
        start_pos: int,
        line_num: int,
    ) -> Token:
        if raw in KWORD:
            return cls._create_token(raw, TokenType.KWORD, start_pos)

        elif raw in KWORD_BAN:
            raise RuntimeError(
                f"Запрещённое ключевое слово '{raw}' на строке {line_num}, позиция {start_pos}"
            )

        else:
            return cls._create_token(raw, TokenType.NAME, start_pos)

    @staticmethod
    def _create_token(
        data: str,
        ttype: TokenType,
        start: int,
        subtype: str | None = None,
    ) -> Token:
        return Token(start=start, data=data, type=ttype, subtype=subtype)

    @staticmethod
    def _is_triple_quote(s: str) -> bool:
        return s in ('"""', "'''")

    @staticmethod
    def _is_string_token(s: str) -> bool:
        if not s:
            return False

        return s[0] in "\"'" or (
            len(s) > 1 and s[0].lower() in "furb" and s[1] in "\"'"
        )

    @staticmethod
    def _is_multiline_string(s: str) -> bool:
        if s[0].lower() in "furb" and s[1] in "\"'":
            quote_part = s[1:]

        else:
            quote_part = s

        return quote_part.startswith(('"""', "'''"))

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
