from pathlib import Path

import pytest

from plg_reader._python.dt import Token, TokenType
from plg_reader._python.parse_file import FileParser


# Вспомогательные функции
def write_temp_file(tmp_path: Path, content: str) -> Path:
    """Записывает строку во временный файл и возвращает путь к нему."""
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")
    return file


def tokens_to_types(tokens: list[Token]) -> list[TokenType]:
    """Возвращает список типов токенов."""
    return [t.type for t in tokens]


def tokens_to_data(tokens: list[Token]) -> list[str]:
    """Возвращает список данных токенов."""
    return [t.data for t in tokens]


def tokens_to_subtypes(tokens: list[Token]) -> list[str | None]:
    """Возвращает список подтипов токенов."""
    return [t.subtype for t in tokens]


def tokens_to_starts(tokens: list[Token]) -> list[int]:
    """Возвращает список стартовых позиций токенов."""
    return [t.start for t in tokens]


# Тесты
class TestFileParser:
    def test_simple_assignment(self, tmp_path):
        code = "x = 1\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)

        assert len(lines) == 1
        line = lines[0]
        assert line.indent == 0
        assert line.line_num == 1
        tokens = line.tokens
        assert tokens_to_types(tokens) == [
            TokenType.NAME,
            TokenType.OP,
            TokenType.NUMBER,
        ]
        assert tokens_to_data(tokens) == ["x", "=", "1"]
        assert tokens_to_starts(tokens) == [0, 2, 4]

    def test_indented_code(self, tmp_path):
        code = "def foo():\n    pass\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)

        assert len(lines) == 2
        assert lines[0].indent == 0
        assert lines[1].indent == 1
        pass_token = lines[1].tokens[0]
        assert pass_token.data == "pass"
        assert pass_token.start == 4

    def test_keywords(self, tmp_path):
        code = "def foo(): pass\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        tokens = lines[0].tokens
        assert tokens_to_types(tokens) == [
            TokenType.KWORD,
            TokenType.NAME,
            TokenType.PARENTHESE_OPEN,
            TokenType.PARENTHESE_CLOSE,
            TokenType.OP,
            TokenType.KWORD,
        ]
        assert tokens_to_data(tokens) == ["def", "foo", "(", ")", ":", "pass"]

    def test_banned_keyword_raises(self, tmp_path):
        code = "def foo():\n    yield x\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(RuntimeError) as exc_info:
            FileParser.parse(file)

        assert "Запрещённое ключевое слово 'yield'" in str(exc_info.value)
        # Позиция на второй строке, отступ 4 пробела
        assert "на строке 2, позиция 4" in str(exc_info.value)

    def test_operators_and_separators(self, tmp_path):
        # Оборачиваем в синтаксически корректное выражение
        code = "x = (1 == 2) != (3 <= 4) >= (5 // 6) ** 7\n...\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        tokens = lines[0].tokens
        tokens.extend(lines[1].tokens)
        subtypes = [t.subtype for t in tokens if t.type == TokenType.OP]
        expected_ops = ["=", "==", "!=", "<=", ">=", "//", "**", "..."]
        for op in expected_ops:
            assert op in subtypes

    def test_parentheses_comma_dot(self, tmp_path):
        code = "x = (1, 2, [3, 4], {5: 6})\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        types = tokens_to_types(lines[0].tokens)
        assert TokenType.PARENTHESE_OPEN in types
        assert TokenType.PARENTHESE_CLOSE in types
        assert TokenType.COMMA in types

        # Отдельно точку
        code2 = "obj.attr\n"
        file2 = write_temp_file(tmp_path, code2)
        lines2 = FileParser.parse(file2)
        assert lines2[0].tokens[1].type == TokenType.DOT

    def test_single_quoted_string(self, tmp_path):
        code = "x = 'hello'\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        str_token = lines[0].tokens[2]
        assert str_token.type == TokenType.STRING
        assert str_token.data == "'hello'"
        assert str_token.start == 4

    def test_double_quoted_string(self, tmp_path):
        code = 'x = "world"\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == '"world"'

    def test_f_string(self, tmp_path):
        code = 'x = f"hello {name}"\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == 'f"hello {name}"'

    def test_raw_string(self, tmp_path):
        code = r'x = r"\n"' + "\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == r'r"\n"'

    def test_triple_quoted_single_line(self, tmp_path):
        code = 'x = """a b c"""\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == '"""a b c"""'
        assert token.start == 4

    def test_triple_quoted_with_prefix(self, tmp_path):
        code = 'x = rf"""raw f"""\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == 'rf"""raw f"""'

    def test_multiline_string_across_lines(self, tmp_path):
        code = 'x = """line1\nline2\nline3"""\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        all_tokens = [t for line in lines for t in line.tokens]
        assert len(all_tokens) == 3  # x, =, MULT_STRING
        token = all_tokens[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == '"""line1\nline2\nline3"""'

    def test_multiline_string_with_prefix_and_indent(self, tmp_path):
        code = 'def foo():\n    x = f"""hello\n    world"""\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        tokens_line2 = lines[1].tokens
        assert len(tokens_line2) == 3
        token = tokens_line2[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == 'f"""hello\n    world"""'
        assert token.start == 8  # позиция 'f' после "    x = "

    def test_multiline_string_closing_quote_with_content(self, tmp_path):
        code = 'x = """doc\nend"""; y = 1\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        tokens = lines[0].tokens
        mult_token = next(t for t in tokens if t.type == TokenType.MULT_STRING)
        assert mult_token.data == '"""doc\nend"""'
        assert any(t.type == TokenType.OP and t.data == ";" for t in tokens)

    def test_comment(self, tmp_path):
        code = "# this is a comment\nx = 1\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[0]
        assert token.type == TokenType.COMMENT
        assert token.data == "# this is a comment"
        assert token.start == 0

    def test_code_with_comment(self, tmp_path):
        code = "x = 1  # comment\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        tokens = lines[0].tokens
        assert tokens[-1].type == TokenType.COMMENT
        assert tokens[-1].data == "# comment"

    @pytest.mark.parametrize("num", ["123", "0x1F", "0b101", "0o77", "3.14", "1_000"])
    def test_numbers(self, tmp_path, num):
        code = f"x = {num}\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.NUMBER
        assert token.data == num

    @pytest.mark.xfail(reason="Комплексные числа пока не реализованы")
    def test_complex_number(self, tmp_path):
        code = "x = 2+3j\n"
        file = write_temp_file(tmp_path, code)
        FileParser.parse(file)
        assert False

    def test_token_positions_with_indent(self, tmp_path):
        code = "def foo():\n    x = 1\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        tokens = lines[1].tokens
        assert tokens[0].start == 4  # 'x'
        assert tokens[1].start == 6  # '='
        assert tokens[2].start == 8  # '1'

    def test_token_positions_multiline_string(self, tmp_path):
        code = 'def foo():\n    x = r"""part1\npart2"""\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[1].tokens[2]
        assert token.start == 8  # позиция 'r' после "    x = "

    def test_empty_line(self, tmp_path):
        code = "\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        assert len(lines) == 1
        assert lines[0].tokens == []
        assert lines[0].indent == 0

    def test_line_with_only_comment(self, tmp_path):
        code = "   # just comment\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        assert len(lines[0].tokens) == 1
        assert lines[0].tokens[0].type == TokenType.COMMENT
        assert lines[0].indent == 0

    def test_strip_comments(self, tmp_path):
        code = "x = 1  # comment\n# another comment\ny = 2\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file, strip_comments=True)
        assert tokens_to_data(lines[0].tokens) == ["x", "=", "1"]
        assert lines[1].tokens == []
        assert tokens_to_data(lines[2].tokens) == ["y", "=", "2"]

    def test_line_continuation(self, tmp_path):
        code = "x = \\\n    1\n"
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        assert len(lines) == 1
        tokens = lines[0].tokens
        assert tokens_to_data(tokens) == ["x", "=", "1"]
        assert tokens[2].start == 4

    def test_line_continuation_with_string(self, tmp_path):
        code = 'x = "multi\\\nline"\n'
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == '"multiline"'

    def test_utf8_bom(self, tmp_path):
        file = tmp_path / "bom.py"
        file.write_bytes(b"\xef\xbb\xbfx = 1\n")
        lines = FileParser.parse(file)
        assert lines[0].tokens[0].data == "x"

    def test_empty_file(self, tmp_path):
        file = write_temp_file(tmp_path, "")
        lines = FileParser.parse(file)
        assert lines == []

    def test_complex_structure(self, tmp_path):
        code = """\
def foo(x):
    \"\"\"Docstring.\"\"\"
    if x > 0:
        return x * 2
    else:
        return -1
"""
        file = write_temp_file(tmp_path, code)
        lines = FileParser.parse(file)
        assert len(lines) == 6
        assert lines[0].tokens[0].data == "def"
        assert lines[1].tokens[0].type == TokenType.MULT_STRING
        assert lines[2].tokens[0].data == "if"
        assert lines[3].indent == 2
