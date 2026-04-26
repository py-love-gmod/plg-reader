from pathlib import Path

import pytest

from plg_reader._python.dt import Token, TokenType
from plg_reader._python.parse_file import FileParser


def write_temp_file(tmp_path: Path, content: str) -> Path:
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")
    return file


def tokens_to_types(tokens: list[Token]) -> list[TokenType]:
    return [t.type for t in tokens]


def tokens_to_data(tokens: list[Token]) -> list[object]:
    return [t.data for t in tokens]


def tokens_to_starts(tokens: list[Token]) -> list[int]:
    return [t.start for t in tokens]


def tokens_to_line_nums(tokens: list[Token]) -> list[int]:
    return [t.line_num for t in tokens]


# Базовые конструкции
class TestSimpleAssignment:
    def test_variable_assignment(self, tmp_path):
        code = "x = 1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
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
        assert tokens_to_data(tokens) == ["x", "=", 1]
        assert tokens_to_starts(tokens) == [0, 2, 4]
        assert tokens_to_line_nums(tokens) == [1, 1, 1]

    def test_multiple_assignments(self, tmp_path):
        code = "a = b = 42\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        assert tokens_to_types(tokens) == [
            TokenType.NAME,
            TokenType.OP,
            TokenType.NAME,
            TokenType.OP,
            TokenType.NUMBER,
        ]
        assert tokens_to_data(tokens) == ["a", "=", "b", "=", 42]


# Ключевые слова, запрещённые слова
class TestKeywords:
    def test_def_and_pass(self, tmp_path):
        code = "def f(): pass\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        assert tokens_to_types(tokens) == [
            TokenType.KWORD,
            TokenType.NAME,
            TokenType.PARENTHESE_OPEN,
            TokenType.PARENTHESE_CLOSE,
            TokenType.OP,
            TokenType.KWORD,
        ]
        assert tokens_to_data(tokens) == ["def", "f", "(", ")", ":", "pass"]

    def test_if_elif_else(self, tmp_path):
        code = "if True:\n    x\nelif False:\n    y\nelse:\n    z\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert lines[0].tokens[0].data == "if"
        assert lines[0].tokens[0].type == TokenType.KWORD
        assert lines[2].tokens[0].data == "elif"
        assert lines[4].tokens[0].data == "else"

    def test_banned_keyword_raises(self, tmp_path):
        code = "def foo():\n    yield x\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(RuntimeError) as exc:
            FileParser.parse(file)

        assert "Запрещённое ключевое слово 'yield'" in str(exc.value)
        assert "на строке 2, позиция 4" in str(exc.value)

    def test_banned_keyword_indented(self, tmp_path):
        code = "def foo():\n    global x\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(RuntimeError) as exc:
            FileParser.parse(file)

        assert "'global'" in str(exc.value)
        assert "на строке 2, позиция 4" in str(exc.value)


# Числа
class TestNumbers:
    @pytest.mark.parametrize(
        "num_str, expected",
        [
            ("0", 0),
            ("123", 123),
            ("0x1F", 31),
            ("0b101", 5),
            ("0o77", 63),
            ("3.14", 3.14),
            ("1_000", 1000),
            ("0b1_0", 2),
            ("0xAB_CD", 0xABCD),
            ("1e3", 1000.0),
            ("1.5e-2", 0.015),
            ("0.5", 0.5),
        ],
    )
    def test_valid_numbers(self, tmp_path, num_str, expected):
        code = f"x = {num_str}\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.NUMBER
        assert token.data == expected
        assert isinstance(token.data, type(expected))

    @pytest.mark.parametrize(
        "num_str, bad_part",
        [
            ("2+3j", "3j"),
            ("3J", "3J"),
            ("10j", "10j"),
        ],
    )
    def test_complex_number_raises(self, tmp_path, num_str, bad_part):
        code = f"x = {num_str}\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(RuntimeError) as exc:
            FileParser.parse(file)

        assert "Комплексные числа не разрешены" in str(exc.value)
        assert bad_part in str(exc.value)

    def test_negative_number_is_op_plus_number(self, tmp_path):
        code = "x = -5\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        assert tokens_to_types(tokens) == [
            TokenType.NAME,
            TokenType.OP,
            TokenType.OP,
            TokenType.NUMBER,
        ]
        assert tokens_to_data(tokens) == ["x", "=", "-", 5]


# Строки
class TestStrings:
    def test_single_quoted(self, tmp_path):
        code = "x = 'hello'\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == "'hello'"
        assert token.start == 4
        assert token.line_num == 1

    def test_double_quoted(self, tmp_path):
        code = 'x = "world"\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == '"world"'

    def test_f_string(self, tmp_path):
        code = 'x = f"hello {name}"\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == 'f"hello {name}"'

    def test_raw_string(self, tmp_path):
        code = r'x = r"\n"' + "\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == r'r"\n"'

    def test_triple_quoted_single_line(self, tmp_path):
        code = 'x = """a b c"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == '"""a b c"""'
        assert token.start == 4

    def test_triple_quoted_with_rf_prefix(self, tmp_path):
        code = 'x = rf"""raw f"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == 'rf"""raw f"""'

    def test_escaped_quote_in_string(self, tmp_path):
        code = "x = 'it\\'s'\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == "'it\\'s'"


# Многострочные строки
class TestMultilineStrings:
    def test_across_multiple_lines(self, tmp_path):
        code = 'x = """line1\nline2\nline3"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        all_tokens = [t for line in lines for t in line.tokens]
        assert len(all_tokens) == 3
        token = all_tokens[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == '"""line1\nline2\nline3"""'

    def test_with_prefix_and_indentation(self, tmp_path):
        code = 'def foo():\n    x = f"""hello\n    world"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens_line2 = lines[1].tokens
        assert len(tokens_line2) == 3
        token = tokens_line2[2]
        assert token.type == TokenType.MULT_STRING
        assert token.data == 'f"""hello\n    world"""'
        assert token.start == 8
        assert token.line_num == 2

    def test_closing_quote_followed_by_code(self, tmp_path):
        code = 'x = """doc\nend"""; y = 1\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        mult = next(t for t in tokens if t.type == TokenType.MULT_STRING)
        assert mult.data == '"""doc\nend"""'
        assert any(t.type == TokenType.OP and t.data == ";" for t in tokens)


# Комментарии
class TestComments:
    def test_full_line_comment(self, tmp_path):
        code = "# this is a comment\nx = 1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        comment_token = lines[0].tokens[0]
        assert comment_token.type == TokenType.COMMENT
        assert comment_token.data == "# this is a comment"
        assert comment_token.start == 0
        assert comment_token.line_num == 1

    def test_inline_comment(self, tmp_path):
        code = "x = 1  # comment\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        assert tokens[-1].type == TokenType.COMMENT
        assert tokens[-1].data == "# comment"

    def test_strip_comments_option(self, tmp_path):
        code = "x = 1  # comment\n# another comment\ny = 2\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code), strip_comments=True)
        assert tokens_to_data(lines[0].tokens) == ["x", "=", 1]
        assert lines[1].tokens == []
        assert tokens_to_data(lines[2].tokens) == ["y", "=", 2]


# Продолжение строки (backslash)
class TestLineContinuation:
    def test_simple_continuation(self, tmp_path):
        code = "x = \\\n    1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 1
        tokens = lines[0].tokens
        assert tokens_to_data(tokens) == ["x", "=", 1]
        assert tokens[0].line_num == 1
        assert tokens[2].line_num == 1
        assert tokens[2].start == 4

    def test_continuation_preserves_indent(self, tmp_path):
        code = "def foo():\n    x = \\\n        1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert lines[1].indent == 1
        tokens = lines[1].tokens
        assert tokens[0].start == 4
        assert tokens[2].start == 8

    def test_continuation_with_string(self, tmp_path):
        code = 'x = "multi\\\nline"\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[2]
        assert token.type == TokenType.STRING
        assert token.data == '"multiline"'


# Координаты токенов (start, line_num)
class TestTokenPositions:
    def test_positions_with_indent(self, tmp_path):
        code = "def foo():\n    x = 1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[1].tokens
        assert tokens[0].start == 4
        assert tokens[0].line_num == 2
        assert tokens[1].start == 6
        assert tokens[2].start == 8

    def test_multiline_string_position(self, tmp_path):
        code = 'def foo():\n    x = r"""part1\npart2"""\n'
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[1].tokens[2]
        assert token.start == 8
        assert token.line_num == 2

    def test_positions_across_continuation(self, tmp_path):
        code = "x = \\\n    1\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        assert tokens[0].line_num == 1
        assert tokens[1].line_num == 1
        assert tokens[2].line_num == 1


# Пустые строки и строки только с комментариями
class TestEmptyAndCommentOnly:
    def test_empty_line(self, tmp_path):
        code = "\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 1
        assert lines[0].tokens == []
        assert lines[0].indent == 0

    def test_blank_line_with_spaces(self, tmp_path):
        code = "   \n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        assert len(lines) == 1
        assert lines[0].tokens == []

    def test_only_comment_line(self, tmp_path):
        code = "   # just a comment\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
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
    def test_all_multi_char_ops(self, tmp_path):
        code = "x += 1; y -= 2; z // 3; a ** 4; b <= 5; c >= 6\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        subtypes = {t.subtype for t in tokens if t.type == TokenType.OP}
        assert "+=" in subtypes
        assert "-=" in subtypes
        assert "//" in subtypes
        assert "**" in subtypes
        assert "<=" in subtypes
        assert ">=" in subtypes
        assert ";" in subtypes

    def test_ellipsis(self, tmp_path):
        code = "...\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        token = lines[0].tokens[0]
        assert token.type == TokenType.OP
        assert token.subtype == "..."
        assert token.data == "..."

    def test_parentheses_and_comma(self, tmp_path):
        code = "(a, b)\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        types = tokens_to_types(lines[0].tokens)
        assert types == [
            TokenType.PARENTHESE_OPEN,
            TokenType.NAME,
            TokenType.COMMA,
            TokenType.NAME,
            TokenType.PARENTHESE_CLOSE,
        ]

    def test_dot_operator(self, tmp_path):
        code = "obj.attr\n"
        lines = FileParser.parse(write_temp_file(tmp_path, code))
        tokens = lines[0].tokens
        assert tokens[1].type == TokenType.DOT
        assert tokens[1].data == "."


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
        assert lines[2].tokens[0].data == "result"
        assert lines[3].tokens[0].data == "if"
        assert lines[4].tokens[0].data == "return"
        assert lines[5].tokens[0].data == "else"
        assert lines[6].tokens[0].data == "return"
        assert lines[1].tokens[0].type == TokenType.MULT_STRING
        assert lines[3].tokens[3].data == 100
        minus_token = lines[6].tokens[1]
        assert minus_token.type == TokenType.OP
        assert minus_token.data == "-"
