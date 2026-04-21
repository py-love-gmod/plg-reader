import pytest

from plg_reader._python.dat_cl import RawLine, Token, TokenType
from plg_reader._python.logic_builder import LineBuilder
from plg_reader._python.raw_line_builder import RawLineBuilder


class TestLineBuilder:
    # Утилиты для создания RawLine
    @staticmethod
    def _make_raw_line(
        raw_strs: list[str],
        indent: int = 0,
        abs_indent: int = 0,
        line_num: int = 1,
        is_string_content: bool = False,
    ) -> RawLine:
        return RawLine(
            indent=indent,
            abs_indent=abs_indent,
            raw_strs=raw_strs,
            line_num=line_num,
            is_string_content=is_string_content,
        )

    # Базовые токены
    def test_simple_assignment(self):
        raw = self._make_raw_line(["x", "=", "1"], abs_indent=0, line_num=1)
        lines = LineBuilder.raw_lines_to_lines([raw])
        assert len(lines) == 1
        line = lines[0]
        assert line.indent == 0
        assert line.line_num == 1
        assert len(line.tokens) == 3

        assert line.tokens[0] == Token(
            start=0, data="x", type=TokenType.NAME, subtype=None
        )
        assert line.tokens[1] == Token(
            start=1, data="=", type=TokenType.OP, subtype="="
        )
        assert line.tokens[2] == Token(
            start=2, data="1", type=TokenType.NUMBER, subtype=None
        )

    def test_indented_code(self):
        raw = self._make_raw_line(["pass"], indent=1, abs_indent=4, line_num=2)
        lines = LineBuilder.raw_lines_to_lines([raw])
        assert lines[0].tokens[0].start == 4

    def test_keywords(self):
        raw = self._make_raw_line(["def", "foo", "(", ")", ":"])
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        assert tokens[0].type == TokenType.KWORD
        assert tokens[0].data == "def"
        assert tokens[1].type == TokenType.NAME
        assert tokens[2].type == TokenType.PARENTHESE_OPEN
        assert tokens[3].type == TokenType.PARENTHESE_CLOSE
        assert tokens[4].type == TokenType.OP
        assert tokens[4].subtype == ":"

    def test_banned_keyword_raises(self):
        raw = self._make_raw_line(["yield"], abs_indent=4, line_num=5)
        with pytest.raises(RuntimeError) as exc_info:
            LineBuilder.raw_lines_to_lines([raw])
        assert "Запрещённое ключевое слово 'yield'" in str(exc_info.value)
        assert "на строке 5, позиция 4" in str(exc_info.value)

    def test_operators_and_separators(self):
        raw = self._make_raw_line(
            ["==", "!=", "<=", ">=", "//", "**", "...", "<<", ">>", ":="]
        )
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        assert all(t.type == TokenType.OP for t in tokens)
        assert [t.subtype for t in tokens] == [
            "==",
            "!=",
            "<=",
            ">=",
            "//",
            "**",
            "...",
            "<<",
            ">>",
            ":=",
        ]

    def test_parentheses_comma_dot(self):
        raw = self._make_raw_line(["(", ")", "[", "]", "{", "}", ",", "."])
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        expected_types = [
            TokenType.PARENTHESE_OPEN,
            TokenType.PARENTHESE_CLOSE,
            TokenType.PARENTHESE_OPEN,
            TokenType.PARENTHESE_CLOSE,
            TokenType.PARENTHESE_OPEN,
            TokenType.PARENTHESE_CLOSE,
            TokenType.COMMA,
            TokenType.DOT,
        ]
        assert [t.type for t in tokens] == expected_types
        assert all(t.subtype is None for t in tokens[:6])

    # Строки
    def test_single_quoted_string(self):
        raw = self._make_raw_line(["x", "=", "'hello'"])
        lines = LineBuilder.raw_lines_to_lines([raw])
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == "'hello'"

    def test_double_quoted_string(self):
        raw = self._make_raw_line(['"world"'])
        lines = LineBuilder.raw_lines_to_lines([raw])
        token = lines[0].tokens[0]
        assert token.type == TokenType.STRING
        assert token.data == '"world"'

    def test_f_string(self):
        raw = self._make_raw_line(["f", '"hello {name}"'])
        lines = LineBuilder.raw_lines_to_lines([raw])
        token = lines[0].tokens[1]
        assert token.type == TokenType.STRING
        assert token.data == '"hello {name}"'

    def test_raw_string(self):
        raw = self._make_raw_line(["r", r'"\n"'])
        lines = LineBuilder.raw_lines_to_lines([raw])
        token = lines[0].tokens[1]
        assert token.type == TokenType.STRING
        assert token.data == r'"\n"'

    def test_triple_quoted_single_line(self):
        raw = self._make_raw_line(['"""', "a b c", '"""'])
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MULT_STRING
        assert tokens[0].data == '"""a b c"""'

    def test_triple_quoted_with_prefix(self):
        raw = self._make_raw_line(["rf", '"""', "raw f", '"""'])
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MULT_STRING
        assert tokens[0].data == 'rf"""raw f"""'

    # Многострочные строки (состояние)
    def test_multiline_string_across_lines(self):
        line1 = self._make_raw_line(['"""', "line1"], abs_indent=0, line_num=1)
        line2 = self._make_raw_line(
            ["line2"], abs_indent=0, line_num=2, is_string_content=True
        )
        line3 = self._make_raw_line(
            ["line3", '"""'], abs_indent=0, line_num=3, is_string_content=False
        )
        lines = LineBuilder.raw_lines_to_lines([line1, line2, line3])
        assert len(lines) == 2
        assert lines[0].tokens == []
        tokens = lines[1].tokens
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MULT_STRING
        assert tokens[0].data == '"""line1line2line3"""'
        assert tokens[0].start == 0

    def test_multiline_string_with_prefix_and_indent(self):
        line1 = self._make_raw_line(["f", '"""', "hello"], abs_indent=4, line_num=1)
        line2 = self._make_raw_line(
            ["world"], abs_indent=0, line_num=2, is_string_content=True
        )
        line3 = self._make_raw_line(
            ['"""'], abs_indent=4, line_num=3, is_string_content=False
        )

        lines = LineBuilder.raw_lines_to_lines([line1, line2, line3])
        assert lines[0].tokens == []
        assert len(lines[1].tokens) == 1
        token = lines[1].tokens[0]
        assert token.type == TokenType.MULT_STRING
        assert token.data == 'f"""helloworld"""'
        assert token.start == 4

    def test_multiline_string_closing_quote_with_content(self):
        line1 = self._make_raw_line(['"""', "doc"], abs_indent=0, line_num=1)
        line2 = self._make_raw_line(
            ["end", '"""', ";"], abs_indent=0, line_num=2, is_string_content=False
        )
        lines = LineBuilder.raw_lines_to_lines([line1, line2])
        assert lines[0].tokens == []
        line2_tokens = lines[1].tokens
        assert len(line2_tokens) == 2
        assert line2_tokens[0].type == TokenType.MULT_STRING
        assert line2_tokens[0].data == '"""docend"""'
        assert line2_tokens[1].type == TokenType.OP
        assert line2_tokens[1].data == ";"

    # Комментарии
    def test_comment(self):
        raw = self._make_raw_line(["# this is a comment"])
        lines = LineBuilder.raw_lines_to_lines([raw])
        token = lines[0].tokens[0]
        assert token.type == TokenType.COMMENT
        assert token.data == "# this is a comment"

    def test_code_with_comment(self):
        raw = self._make_raw_line(["x", "=", "1", "# comment"])
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        assert tokens[-1].type == TokenType.COMMENT

    # Числа
    @pytest.mark.parametrize("num", ["123", "0x1F", "0b101", "0o77", "3.14", "1_000"])
    def test_numbers(self, num):
        raw = self._make_raw_line([num])
        lines = LineBuilder.raw_lines_to_lines([raw])
        token = lines[0].tokens[0]
        assert token.type == TokenType.NUMBER
        assert token.data == num

    @pytest.mark.xfail(reason="Комплексные числа пока не реализованы")
    def test_complex_number(self):
        raw = self._make_raw_line(["2+3j"])
        LineBuilder.raw_lines_to_lines([raw])
        assert False

    # Позиции токенов (start)
    def test_token_positions_with_indent(self):
        raw = self._make_raw_line(["x", "=", "1"], indent=1, abs_indent=4, line_num=1)
        lines = LineBuilder.raw_lines_to_lines([raw])
        tokens = lines[0].tokens
        assert tokens[0].start == 4
        assert tokens[1].start == 5
        assert tokens[2].start == 6

    def test_token_positions_multiline_string(self):
        line1 = self._make_raw_line(["r", '"""', "part1"], abs_indent=4, line_num=1)
        line2 = self._make_raw_line(
            ["part2", '"""'], abs_indent=0, line_num=2, is_string_content=False
        )
        lines = LineBuilder.raw_lines_to_lines([line1, line2])
        token = lines[1].tokens[0]
        assert token.start == 4

    # Пустые строки и строки без токенов
    def test_empty_line(self):
        raw = self._make_raw_line([], line_num=1)
        lines = LineBuilder.raw_lines_to_lines([raw])
        assert len(lines) == 1
        assert lines[0].tokens == []

    def test_is_string_content_lines_are_skipped_in_output(self):
        line1 = self._make_raw_line(['"""'], line_num=1)
        line2 = self._make_raw_line(["content"], line_num=2, is_string_content=True)
        line3 = self._make_raw_line(['"""'], line_num=3)
        lines = LineBuilder.raw_lines_to_lines([line1, line2, line3])
        assert len(lines) == 2
        assert lines[0].line_num == 1
        assert lines[1].line_num == 3

    # Интеграция с реальным RawLineBuilder (опционально)
    def test_with_raw_line_builder(self, tmp_path):
        code = "def foo():\n    x = 1\n"
        file = tmp_path / "test.py"
        file.write_text(code, encoding="utf-8")
        raw_lines = RawLineBuilder.read_file_to_raw_lines(file)
        lines = LineBuilder.raw_lines_to_lines(raw_lines)

        assert len(lines) == 2
        assert lines[0].tokens[0].data == "def"
        assert lines[0].tokens[0].type == TokenType.KWORD
        assert lines[1].tokens[0].start == 4
