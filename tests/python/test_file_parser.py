from pathlib import Path

import pytest

from plg_reader._python.dt import TokenType
from plg_reader._python.parse_file import FileParser


def write_temp_file(tmp_path: Path, content: str) -> Path:
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")
    return file


# Простейшие присваивания и координаты
class TestSimpleAssignment:
    def test_single_assignment(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x = 1\n"))
        assert len(lines) == 1
        line = lines[0]
        assert line.indent == 0
        assert line.line_num == 1
        assert [t.type for t in line.tokens] == [
            TokenType.NAME,
            TokenType.OP,
            TokenType.NUMBER,
        ]
        assert [t.data for t in line.tokens] == ["x", "=", 1]
        assert [t.pos for t in line.tokens] == [(1, 0), (1, 2), (1, 4)]

    def test_multiple_assignments(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "a = b = 42\n"))
        tokens = lines[0].tokens
        assert [t.type for t in tokens] == [
            TokenType.NAME,
            TokenType.OP,
            TokenType.NAME,
            TokenType.OP,
            TokenType.NUMBER,
        ]
        assert [t.data for t in tokens] == ["a", "=", "b", "=", 42]
        assert tokens[4].pos == (1, 8)

    def test_chained_operators(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x += 1; y -= 2\n"))
        assert len(lines) == 2
        assert [t.data for t in lines[0].tokens] == ["x", "+=", 1]
        assert [t.data for t in lines[1].tokens] == ["y", "-=", 2]
        assert lines[0].tokens[2].pos == (1, 5)
        assert lines[1].tokens[2].pos == (1, 13)


# Ключевые слова и запрещённые
class TestKeywords:
    def test_common_keywords(self, tmp_path):
        code = "def f():\n    return True\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert lines[0].tokens[0].data == "def"
        assert lines[0].tokens[0].type == TokenType.KWORD
        assert lines[1].tokens[0].data == "return"
        assert lines[1].tokens[0].type == TokenType.KWORD
        assert lines[1].tokens[1].data == "True"
        assert lines[1].tokens[1].type == TokenType.KWORD

    def test_banned_keyword_raises(self, tmp_path):
        code = "def f():\n    yield x\n"
        with pytest.raises(
            RuntimeError,
            match="Запрещённое ключевое слово 'yield' на строке 2, позиция 4",
        ):
            FileParser.parse(write_temp_file(tmp_path, code))

    def test_banned_keyword_indented(self, tmp_path):
        code = "def f():\n    global x\n"
        with pytest.raises(
            RuntimeError,
            match="Запрещённое ключевое слово 'global' на строке 2, позиция 4",
        ):
            FileParser.parse(write_temp_file(tmp_path, code))


# Числа
class TestNumbers:
    @pytest.mark.parametrize(
        "num_str, expected",
        [
            ("123", 123),
            ("0x1F", 31),
            ("0b101", 5),
            ("0o77", 63),
            ("3.14", 3.14),
            ("1_000", 1000),
            ("1e3", 1000.0),
            ("1.5e-2", 0.015),
        ],
    )
    def test_valid_numbers(self, tmp_path, num_str, expected):
        lines = FileParser.parse(write_temp_file(tmp_path, f"x = {num_str}\n"))
        token = lines[0].tokens[2]
        assert token.type == TokenType.NUMBER
        assert token.data == expected

    def test_complex_numbers_raise(self, tmp_path):
        with pytest.raises(RuntimeError, match="Комплексные числа не разрешены"):
            FileParser.parse(write_temp_file(tmp_path, "x = 3j\n"))

    def test_negative_number(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x = -5\n"))
        tokens = lines[0].tokens
        assert [t.type for t in tokens] == [
            TokenType.NAME,
            TokenType.OP,
            TokenType.OP,
            TokenType.NUMBER,
        ]
        assert tokens[2].data == "-"
        assert tokens[3].data == 5

    def test_number_with_underscores(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x = 0b1_0\n"))
        assert lines[0].tokens[2].data == 2


# Строки
class TestStrings:
    def test_single_quoted(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x = 'hello'\n"))
        t = lines[0].tokens[2]
        assert t.type == TokenType.STRING
        assert t.data == "'hello'"
        assert t.pos == (1, 4)

    def test_double_quoted(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, 'x = "world"\n'))
        t = lines[0].tokens[2]
        assert t.type == TokenType.STRING
        assert t.data == '"world"'

    def test_f_string(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, 'x = f"val={1}"\n'))
        t = lines[0].tokens[2]
        assert t.type == TokenType.STRING
        assert t.data == 'f"val={1}"'

    def test_raw_string(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, r'x = r"\n"' + "\n"))
        t = lines[0].tokens[2]
        assert t.type == TokenType.STRING
        assert t.data == r'r"\n"'

    def test_triple_quoted_single_line(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, 'x = """abc"""\n'))
        t = lines[0].tokens[2]
        assert t.type == TokenType.MULT_STRING
        assert t.data == '"""abc"""'

    def test_triple_with_prefix(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, 'x = rf"""raw f"""\n'))
        t = lines[0].tokens[2]
        assert t.type == TokenType.MULT_STRING
        assert t.data == 'rf"""raw f"""'

    def test_escaped_quote(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x = 'it\\'s'\n"))
        t = lines[0].tokens[2]
        assert t.data == "'it\\'s'"


# Многострочные строки
class TestMultilineStrings:
    def test_across_lines(self, tmp_path):
        code = 'x = """line1\nline2\nline3"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 1
        tokens = lines[0].tokens
        assert len(tokens) == 3
        assert tokens[2].type == TokenType.MULT_STRING
        assert tokens[2].data == '"""line1\nline2\nline3"""'
        assert tokens[2].pos[0] == 1

    def test_with_indent(self, tmp_path):
        code = 'def f():\n    x = """hello\n    world"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        mult = lines[1].tokens[2]
        assert mult.type == TokenType.MULT_STRING
        assert mult.data == '"""hello\n    world"""'
        assert mult.pos == (2, 8)

    def test_closing_quote_followed_by_code(self, tmp_path):
        code = 'x = """doc\nend"""; y = 1\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 3
        assert [t.data for t in lines[0].tokens] == ["x", "=", '"""doc\nend"""']
        assert lines[1].tokens == []
        assert [t.data for t in lines[2].tokens] == ["y", "=", 1]


# Комментарии
class TestComments:
    def test_full_line_comment(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "# comment\nx = 1\n"))
        assert lines[0].tokens[0].type == TokenType.COMMENT
        assert lines[0].tokens[0].data == "# comment"
        assert lines[0].tokens[0].pos == (1, 0)

    def test_inline_comment(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "x = 1  # inline\n"))
        assert lines[0].tokens[-1].type == TokenType.COMMENT
        assert lines[0].tokens[-1].data == "# inline"

    def test_strip_comments_option(self, tmp_path):
        code = "x = 1  # comment\n# another\ny = 2\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code), strip_comments=True)
        assert len(lines) == 3
        assert [t.data for t in lines[0].tokens] == ["x", "=", 1]
        assert lines[1].tokens == []
        assert [t.data for t in lines[2].tokens] == ["y", "=", 2]


# Продолжение строки (\)
class TestLineContinuation:
    def test_simple(self, tmp_path):
        code = "x = \\\n    1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 1
        tokens = lines[0].tokens
        assert tokens[2].data == 1
        assert tokens[2].pos == (2, 4)

    def test_with_indent(self, tmp_path):
        code = "def f():\n    x = \\\n        1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert lines[1].indent == 1
        assert lines[1].tokens[2].pos == (3, 8)

    def test_inside_string(self, tmp_path):
        code = 'x = "multi\\\nline"\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        t = lines[0].tokens[2]
        assert "multiline" in t.data


# Разбивка по ';'
class TestSemicolon:
    def test_simple_split(self, tmp_path):
        code = "a = 1; b = 2\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 2
        assert [t.data for t in lines[0].tokens] == ["a", "=", 1]
        assert [t.data for t in lines[1].tokens] == ["b", "=", 2]
        assert lines[1].tokens[0].pos == (1, 7)

    def test_with_comment(self, tmp_path):
        code = "x = 1; # comment\ny = 2\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 3
        assert [t.data for t in lines[0].tokens] == ["x", "=", 1]
        assert [t.type for t in lines[1].tokens] == [TokenType.COMMENT]
        assert lines[1].tokens[0].data == "# comment"
        assert [t.data for t in lines[2].tokens] == ["y", "=", 2]


# Пустые строки и только комментарии
class TestEmptyLines:
    def test_empty_line(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "\n"))
        assert len(lines) == 1
        assert lines[0].tokens == []

    def test_blank_line(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "   \n"))
        assert len(lines) == 1
        assert lines[0].tokens == []

    def test_only_comment(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "   # just comment\n"))
        assert len(lines[0].tokens) == 1
        assert lines[0].tokens[0].type == TokenType.COMMENT
        assert lines[0].indent == 0


# UTF-8 BOM и пустой файл
class TestFileFeatures:
    def test_utf8_bom(self, tmp_path):
        file = tmp_path / "bom.py"
        file.write_bytes(b"\xef\xbb\xbfx = 1\n")
        lines = FileParser.parse(file)
        assert lines[0].tokens[0].data == "x"

    def test_empty_file(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, ""))
        assert lines == []


# Операторы и разделители
class TestOperatorsAndSeparators:
    def test_parentheses_and_comma(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "(a, b)\n"))
        tokens = lines[0].tokens
        assert tokens[0].type == TokenType.PARENTHESE_OPEN
        assert tokens[2].type == TokenType.COMMA
        assert tokens[4].type == TokenType.PARENTHESE_CLOSE

    def test_dot_operator(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "obj.attr\n"))
        assert lines[0].tokens[1].type == TokenType.DOT
        assert lines[0].tokens[1].data == "."

    def test_ellipsis(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "...\n"))
        t = lines[0].tokens[0]
        assert t.type == TokenType.OP
        assert t.subtype == "..."

    def test_compound_operators(self, tmp_path):
        code = "x += 1; y -= 2; z // 3\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        subtypes = [
            t.subtype for line in lines for t in line.tokens if t.type == TokenType.OP
        ]
        assert "+=" in subtypes
        assert "-=" in subtypes
        assert "//" in subtypes


# Интеграционный тест
class TestComplexStructure:
    def test_full_function(self, tmp_path):
        code = """\
def multiply(x, y):
    \"\"\"Multiply two numbers.\"\"\"
    result = x * y
    if result > 100:
        return result
    else:
        return -1
"""
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 7
        assert lines[0].tokens[0].data == "def"
        assert lines[1].tokens[0].type == TokenType.MULT_STRING
        assert lines[2].tokens[0].data == "result"
        assert lines[3].tokens[0].data == "if"
        assert lines[4].tokens[0].data == "return"
        assert lines[5].tokens[0].data == "else"
        assert lines[6].tokens[0].data == "return"
        assert lines[3].tokens[3].data == 100
        minus = lines[6].tokens[1]
        assert minus.type == TokenType.OP and minus.data == "-"
