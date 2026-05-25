from pathlib import Path

import pytest

from plg_reader._python.file_parse_dt import TokenType
from plg_reader._python.file_parser import FileParser


def write_temp_file(tmp_path: Path, content: str) -> Path:
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")
    return file


# Простые присваивания
def test_single_assignment(tmp_path):
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


def test_multiple_assignments(tmp_path):
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


def test_chained_operators(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x += 1; y -= 2\n"))
    assert len(lines) == 2
    assert [t.data for t in lines[0].tokens] == ["x", "+=", 1]
    assert [t.data for t in lines[1].tokens] == ["y", "-=", 2]
    assert lines[0].tokens[2].pos == (1, 5)
    assert lines[1].tokens[2].pos == (1, 13)


# Ключевые слова
def test_common_keywords(tmp_path):
    code = "def f():\n    return True\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert lines[0].tokens[0].data == "def"
    assert lines[0].tokens[0].type == TokenType.KWORD
    assert lines[1].tokens[0].data == "return"
    assert lines[1].tokens[0].type == TokenType.KWORD
    assert lines[1].tokens[1].data == "True"
    assert lines[1].tokens[1].type == TokenType.KWORD


@pytest.mark.parametrize(
    "code, keyword, line, pos",
    [
        ("def f():\n    yield x\n", "yield", 2, 4),
        ("def f():\n    global x\n", "global", 2, 4),
    ],
)
def test_banned_keyword_raises(tmp_path, code, keyword, line, pos):
    with pytest.raises(
        RuntimeError,
        match=f"Запрещённое ключевое слово '{keyword}' на строке {line}, позиция {pos}",
    ):
        FileParser.parse(write_temp_file(tmp_path, code))


# Числа
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
def test_valid_numbers(tmp_path, num_str, expected):
    lines = FileParser.parse(write_temp_file(tmp_path, f"x = {num_str}\n"))
    token = lines[0].tokens[2]
    assert token.type == TokenType.NUMBER
    assert token.data == expected


def test_complex_numbers_raise(tmp_path):
    with pytest.raises(RuntimeError, match="Комплексные числа не разрешены"):
        FileParser.parse(write_temp_file(tmp_path, "x = 3j\n"))


def test_negative_number(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = -5\n"))
    tokens = lines[0].tokens
    assert [t.type for t in tokens] == [
        TokenType.NAME,
        TokenType.OP,
        TokenType.NUMBER,
    ]
    assert tokens[2].data == -5


def test_number_with_underscores(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = 0b1_0\n"))
    assert lines[0].tokens[2].data == 2


# Строки и f‑строки
@pytest.mark.parametrize(
    "code, expected_type, expected_data",
    [
        ("x = 'hello'\n", TokenType.STRING, ("", "'hello'")),
        ('x = "world"\n', TokenType.STRING, ("", '"world"')),
        (r'x = r"\n"' + "\n", TokenType.STRING, ("r", '"\\n"')),
        ("x = b'ABC'\n", TokenType.STRING, ("b", "'ABC'")),
        ("x = rb'ABC'\n", TokenType.STRING, ("rb", "'ABC'")),
        ("x = 'it\\'s'\n", TokenType.STRING, ("", "'it\\'s'")),
    ],
)
def test_string_literals(tmp_path, code, expected_type, expected_data):
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    t = lines[0].tokens[2]
    assert t.type == expected_type
    assert t.data == expected_data


def test_triple_quoted_single_line(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, 'x = """abc"""\n'))
    t = lines[0].tokens[2]
    assert t.type == TokenType.STRING
    assert t.data == ("", '"""abc"""')


def test_triple_with_prefix(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, 'x = rf"""raw f"""\n'))
    t = lines[0].tokens[2]
    assert t.type == TokenType.FORMATTED_STRING
    assert t.data == ("rf", ["raw f"])


# f‑строки
@pytest.mark.parametrize(
    "code, prefix, part_count, first_part",
    [
        ('x = f"val={1}"\n', "f", 2, "val="),
        ('x = f"hello {world} and {1+2}"\n', "f", 4, "hello "),
        ('x = f"{1+2}"\n', "f", 1, None),  # только выражение
        ('x = f"{var=}"\n', "f", 1, None),
        ('x = f"value: {{1+2}}"\n', "f", 1, "value: {1+2}"),
    ],
)
def test_fstrings(tmp_path, code, prefix, part_count, first_part):
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    t = lines[0].tokens[2]
    assert t.type == TokenType.FORMATTED_STRING
    pfx, parts = t.data
    assert pfx == prefix
    assert len(parts) == part_count
    if first_part is not None:
        assert parts[0] == first_part


# Многострочные строки и f‑строки
def test_multiline_string_across_lines(tmp_path):
    code = 'x = """line1\nline2\nline3"""\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    tokens = lines[0].tokens
    assert len(tokens) == 3
    assert tokens[2].type == TokenType.STRING
    assert tokens[2].data == ("", '"""line1\nline2\nline3"""')
    assert tokens[2].pos[0] == 1


def test_multiline_string_with_indent(tmp_path):
    code = 'def f():\n    x = """hello\n    world"""\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 2
    mult = lines[1].tokens[2]
    assert mult.type == TokenType.STRING
    assert mult.data == ("", '"""hello\n    world"""')
    assert mult.pos == (2, 8)


def test_multiline_string_closing_followed_by_code(tmp_path):
    code = 'x = """doc\nend"""; y = 1\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 2
    assert [t.data for t in lines[0].tokens] == ["x", "=", ("", '"""doc\nend"""')]
    assert [t.data for t in lines[1].tokens] == ["y", "=", 1]


def test_multiline_fstring(tmp_path):
    code = 'x = f"""line {1}\nline {2}"""\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    t = lines[0].tokens[2]
    assert t.type == TokenType.FORMATTED_STRING
    prefix, parts = t.data
    assert prefix == "f"
    assert len(parts) == 4
    assert parts[0] == "line "
    assert isinstance(parts[1], list)
    assert parts[2] == "\nline "
    assert isinstance(parts[3], list)


def test_multiline_fstring_with_trailing_code(tmp_path):
    code = 'x = f"""start {1}\nend""" ; y = 1\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 2
    t = lines[0].tokens[2]
    assert t.type == TokenType.FORMATTED_STRING
    prefix, parts = t.data
    assert parts[0] == "start "
    assert isinstance(parts[1], list)
    assert parts[2] == "\nend"
    assert lines[1].tokens[0].data == "y"


# Комментарии
def test_full_line_comment(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "# comment\nx = 1\n"))
    assert lines[0].tokens[0].type == TokenType.COMMENT
    assert lines[0].tokens[0].data == "# comment"
    assert lines[0].tokens[0].pos == (1, 0)


def test_inline_comment(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = 1  # inline\n"))
    assert lines[0].tokens[-1].type == TokenType.COMMENT
    assert lines[0].tokens[-1].data == "# inline"


def test_strip_comments_option(tmp_path):
    code = "x = 1  # comment\n# another\ny = 2\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code), strip_comments=True)
    assert len(lines) == 3
    assert [t.data for t in lines[0].tokens] == ["x", "=", 1]
    assert lines[1].tokens == []
    assert [t.data for t in lines[2].tokens] == ["y", "=", 2]


# Продолжение строк
def test_line_continuation_simple(tmp_path):
    code = "x = \\\n    1\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    tokens = lines[0].tokens
    assert tokens[2].data == 1
    assert tokens[2].pos == (2, 4)


def test_line_continuation_with_indent(tmp_path):
    code = "def f():\n    x = \\\n        1\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert lines[1].indent == 1
    assert lines[1].tokens[2].pos == (3, 8)


def test_line_continuation_inside_string(tmp_path):
    code = 'x = "multi\\\nline"\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    t = lines[0].tokens[2]
    assert t.data[1] == '"multiline"'


# Точка с запятой
def test_semicolon_split(tmp_path):
    code = "a = 1; b = 2\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 2
    assert [t.data for t in lines[0].tokens] == ["a", "=", 1]
    assert [t.data for t in lines[1].tokens] == ["b", "=", 2]
    assert lines[1].tokens[0].pos == (1, 7)


def test_semicolon_with_comment(tmp_path):
    code = "x = 1; # comment\ny = 2\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 3
    assert [t.data for t in lines[0].tokens] == ["x", "=", 1]
    assert [t.type for t in lines[1].tokens] == [TokenType.COMMENT]
    assert lines[1].tokens[0].data == "# comment"
    assert [t.data for t in lines[2].tokens] == ["y", "=", 2]


# Пустые строки
def test_empty_line(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "\n"))
    assert len(lines) == 1
    assert lines[0].tokens == []


def test_blank_line(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "   \n"))
    assert len(lines) == 1
    assert lines[0].tokens == []


def test_only_comment_line(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "   # just comment\n"))
    assert len(lines[0].tokens) == 1
    assert lines[0].tokens[0].type == TokenType.COMMENT
    assert lines[0].indent == 1


# Особые файлы
def test_utf8_bom(tmp_path):
    file = tmp_path / "bom.py"
    file.write_bytes(b"\xef\xbb\xbfx = 1\n")
    lines = FileParser.parse(file)
    assert lines[0].tokens[0].data == "x"


def test_empty_file(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, ""))
    assert lines == []


# Операторы и разделители
def test_parentheses_and_comma(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "(a, b)\n"))
    tokens = lines[0].tokens
    assert tokens[0].type == TokenType.PARENTHESE_OPEN
    assert tokens[2].type == TokenType.COMMA
    assert tokens[4].type == TokenType.PARENTHESE_CLOSE


def test_dot_operator(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "obj.attr\n"))
    assert lines[0].tokens[1].type == TokenType.DOT
    assert lines[0].tokens[1].data == "."


def test_ellipsis(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "...\n"))
    t = lines[0].tokens[0]
    assert t.type == TokenType.OP
    assert t.data == "..."


def test_compound_operators(tmp_path):
    code = "x += 1; y -= 2; z // 3\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    ops = [t.data for line in lines for t in line.tokens if t.type == TokenType.OP]
    assert "+=" in ops
    assert "-=" in ops
    assert "//" in ops


# Неявное продолжение строк внутри скобок
def test_parentheses_across_lines(tmp_path):
    code = "x = (\n    1,\n    2,\n)\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    tokens = lines[0].tokens
    assert tokens[0].data == "x"
    assert tokens[1].data == "="
    assert tokens[2].type == TokenType.PARENTHESE_OPEN
    assert tokens[2].pos == (1, 4)
    assert tokens[3].data == 1
    assert tokens[3].pos[0] == 2
    assert tokens[5].data == 2
    assert tokens[5].pos[0] == 3
    assert tokens[7].type == TokenType.PARENTHESE_CLOSE
    assert tokens[7].pos[0] == 4


def test_list_across_lines(tmp_path):
    code = "items = [\n    'a',\n    'b',\n]\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    tokens = lines[0].tokens
    assert tokens[2].type == TokenType.PARENTHESE_OPEN


def test_nested_brackets_across_lines(tmp_path):
    code = "x = {\n    'a': [1, 2],\n    'b': (3, 4),\n}\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1


# Краевые случаи
def test_unary_vs_binary_minus(tmp_path):
    code = "x = -5 + -3.14 - 2\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    tokens = lines[0].tokens
    assert [t.type for t in tokens] == [
        TokenType.NAME,
        TokenType.OP,
        TokenType.NUMBER,
        TokenType.OP,
        TokenType.NUMBER,
        TokenType.OP,
        TokenType.NUMBER,
    ]
    assert [t.data for t in tokens] == ["x", "=", -5, "+", -3.14, "-", 2]


def test_comment_disables_continuation(tmp_path):
    code = "x = 1 # comment \\\ny = 2\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 2
    assert lines[0].tokens[-1].type == TokenType.COMMENT
    assert lines[1].tokens[0].data == "y"


def test_semicolon_no_empty_group(tmp_path):
    code = "x = 1  ;\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    assert [t.data for t in lines[0].tokens] == ["x", "=", 1]


# Дополнительные проверки чисел и отступов
def test_hex_number(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = 0xFF\n"))
    assert lines[0].tokens[2].data == 255


def test_bin_number(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = 0b101\n"))
    assert lines[0].tokens[2].data == 5


def test_oct_number(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = 0o77\n"))
    assert lines[0].tokens[2].data == 63


def test_comment_with_changing_indent(tmp_path):
    code = "if True:\n    # inner comment\n    pass\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert lines[1].indent == 1
    assert lines[1].tokens[0].type == TokenType.COMMENT
    assert lines[2].indent == 1


def test_dedent_after_comment_block(tmp_path):
    code = "if True:\n    # comment\n    x = 1\npass\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert lines[0].indent == 0
    assert lines[1].indent == 1
    assert lines[1].tokens[0].type == TokenType.COMMENT
    assert lines[2].indent == 1
    assert lines[3].indent == 0


def test_trailing_comma_in_parentheses(tmp_path):
    code = "x = (1,)\n"
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    tokens = lines[0].tokens
    assert tokens[2].type == TokenType.PARENTHESE_OPEN
    assert tokens[3].data == 1
    assert tokens[4].type == TokenType.COMMA
    assert tokens[5].type == TokenType.PARENTHESE_CLOSE


def test_unary_plus(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = +5\n"))
    tokens = lines[0].tokens
    assert len(tokens) == 3
    assert tokens[2].type == TokenType.NUMBER
    assert tokens[2].data == 5
    assert tokens[2].pos == (1, 4)


def test_unary_minus_after_operator(tmp_path):
    lines = FileParser.parse(write_temp_file(tmp_path, "x = 5 - -3\n"))
    tokens = lines[0].tokens
    assert [t.data for t in tokens] == ["x", "=", 5, "-", -3]
    assert tokens[3].type == TokenType.OP
    assert tokens[4].type == TokenType.NUMBER


def test_multiline_string_with_code_after_closing(tmp_path):
    code = 'x = """hello\\nworld""" + "!"\n'
    lines = FileParser.parse(write_temp_file(tmp_path, code))
    assert len(lines) == 1
    tokens = lines[0].tokens
    assert tokens[2].type == TokenType.STRING
    assert tokens[3].data == "+"
    assert tokens[4].type == TokenType.STRING


def test_full_function(tmp_path):
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
    assert lines[1].tokens[0].type == TokenType.STRING
    assert lines[2].tokens[0].data == "result"
    assert lines[3].tokens[0].data == "if"
    assert lines[4].tokens[0].data == "return"
    assert lines[5].tokens[0].data == "else"
    assert lines[6].tokens[0].data == "return"
    assert lines[3].tokens[3].data == 100
    assert lines[6].tokens[1].data == -1
