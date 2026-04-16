import pytest

from plg_reader._python_reader.raw_line_builder import RawLineBuilder


def write_temp_file(tmp_path, content):
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")
    return file


class TestRawLineBuilder:
    # Базовые конструкции
    def test_simple_assignment(self, tmp_path):
        code = "x = 1\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 1
        assert result[0].indent == 0
        assert result[0].raw_strs == ["x", "=", "1"]
        assert result[0].is_string_content is False

    def test_indented_block(self, tmp_path):
        code = "def foo():\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 2
        assert result[0].indent == 0
        assert result[0].raw_strs == ["def", "foo", "(", ")", ":"]
        assert result[1].indent == 1
        assert result[1].raw_strs == ["pass"]

    def test_spaces_indent(self, tmp_path):
        code = "def foo():\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[1].indent == 1

    def test_tabs_indent(self, tmp_path):
        code = "def foo():\n\tpass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[1].indent == 1

    def test_multiple_dedent(self, tmp_path):
        code = "if True:\n    if False:\n        pass\n    else:\n        pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        levels = [line.indent for line in result]
        assert levels == [0, 1, 2, 1, 2]

    def test_empty_lines_preserved(self, tmp_path):
        code = "def foo():\n\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 3
        assert result[0].raw_strs == ["def", "foo", "(", ")", ":"]
        assert result[1].raw_strs == []
        assert result[2].raw_strs == ["pass"]
        assert [line.indent for line in result] == [0, 0, 1]

    # Строковые литералы
    def test_single_quoted_string(self, tmp_path):
        code = "x = 'hello world'\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", "'hello world'"]

    def test_double_quoted_string(self, tmp_path):
        code = 'x = "hello world"\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", '"hello world"']

    def test_string_with_escape(self, tmp_path):
        code = 'x = "hello\\nworld"\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", '"hello\\nworld"']

    def test_string_with_quotes_inside(self, tmp_path):
        code = r'x = "he said \"hello\""' + "\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", r'"he said \"hello\""']

    def test_f_string(self, tmp_path):
        code = 'f"hello {name}"\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["f", '"hello {name}"']

    def test_raw_string(self, tmp_path):
        code = r'r"\n"' + "\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["r", r'"\n"']

    def test_combined_prefix_rf(self, tmp_path):
        code = 'rf"raw f-string {value}"\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["rf", '"raw f-string {value}"']

    # Многострочные строки (тройные кавычки)
    def test_triple_quoted_single_line(self, tmp_path):
        code = '"""a b c"""\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 1
        assert result[0].raw_strs == ['"""', "a b c", '"""']
        assert result[0].is_string_content is False

    def test_triple_quoted_multiline(self, tmp_path):
        code = '"""line1\nline2"""\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 2
        assert result[0].raw_strs == ['"""', "line1"]
        assert result[1].raw_strs == ["line2", '"""']
        assert result[0].is_string_content is False
        assert result[1].is_string_content is False

    def test_triple_quoted_with_blank_lines(self, tmp_path):
        code = '"""\n\n"""\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 3
        assert result[0].raw_strs == ['"""']
        assert result[1].raw_strs == [""]
        assert result[2].raw_strs == ['"""']
        assert result[1].is_string_content is True

    def test_triple_quoted_with_indent(self, tmp_path):
        code = '''def foo():
    """
    docstring
    """
    pass
'''
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 5
        assert result[0].indent == 0
        assert result[0].raw_strs == ["def", "foo", "(", ")", ":"]
        assert result[1].indent == 1
        assert result[1].raw_strs == ['"""']
        assert result[2].indent == 1
        assert result[2].raw_strs == ["    docstring"]
        assert result[3].indent == 1
        assert result[3].raw_strs == ['"""']
        assert result[4].indent == 1
        assert result[4].raw_strs == ["pass"]
        assert result[2].is_string_content is True

    # Комментарии
    def test_comment_only_line(self, tmp_path):
        code = "# just a comment\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["# just a comment"]

    def test_comment_after_code(self, tmp_path):
        code = "x = 1  # comment\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", "1", "# comment"]

    # Продолжение строк (обратный слеш)
    def test_line_continuation(self, tmp_path):
        code = "x = 1 + \\\n    2\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert len(result) == 1
        assert result[0].raw_strs == ["x", "=", "1", "+", "2"]

    # Операторы и разделители
    def test_operators_and_brackets(self, tmp_path):
        code = "a = (1 + 2) * 3\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["a", "=", "(", "1", "+", "2", ")", "*", "3"]

    def test_multi_char_operators(self, tmp_path):
        code = "x == y != z <= w >= v // u ** t << r\n"  #
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == [
            "x",
            "==",
            "y",
            "!=",
            "z",
            "<=",
            "w",
            ">=",
            "v",
            "//",
            "u",
            "**",
            "t",
            "<<",
            "r",
        ]

    def test_arrow_operator_in_function(self, tmp_path):
        code = "def f() -> int: pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["def", "f", "(", ")", "->", "int", ":", "pass"]

    # Декораторы, async, match
    def test_decorator(self, tmp_path):
        code = "@deco\ndef foo():\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["@", "deco"]
        assert result[1].raw_strs == ["def", "foo", "(", ")", ":"]

    def test_async_function(self, tmp_path):
        code = "async def foo():\n    await bar()\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["async", "def", "foo", "(", ")", ":"]
        assert result[1].raw_strs == ["await", "bar", "(", ")"]

    def test_match_case(self, tmp_path):
        code = "match x:\n    case 1:\n        pass\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert [line.indent for line in result] == [0, 1, 2]

    # Обработка ошибок
    def test_syntax_error_raises(self, tmp_path):
        code = "def foo(\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(SyntaxError):
            RawLineBuilder.read_file_to_tokens(file)

    def test_inconsistent_indent_raises(self, tmp_path):
        code = "if True:\n  pass\n   pass\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(SyntaxError):
            RawLineBuilder.read_file_to_tokens(file)

    # Пустые файлы и BOM
    def test_empty_file(self, tmp_path):
        code = ""
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result == []

    def test_utf8_bom(self, tmp_path):
        code = "x = 1\n"
        file = tmp_path / "test.py"
        file.write_bytes(b"\xef\xbb\xbf" + code.encode("utf-8"))
        result = RawLineBuilder.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", "1"]

    # Отступы внутри строк не влияют на уровень
    def test_indent_inside_string_does_not_affect_level(self, tmp_path):
        code = '''def foo():
    x = 1
    """
        This indent should not increase block level
    """
    y = 2
'''
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file)
        levels = [line.indent for line in result if not line.is_string_content]
        assert levels == [0, 1, 1, 1, 1]
        string_line = result[3]
        assert string_line.is_string_content is True
        assert string_line.indent == 1

    # Тесты для strip_comments=True

    def test_strip_comments_removes_comment_tokens(self, tmp_path):
        code = "x = 1  # comment\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert len(result) == 1
        assert result[0].raw_strs == ["x", "=", "1"]

    def test_strip_comments_removes_only_comment_lines(self, tmp_path):
        code = "# comment line\nx = 1\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert len(result) == 2
        assert result[0].raw_strs == []
        assert result[1].raw_strs == ["x", "=", "1"]

    def test_strip_comments_preserves_empty_lines(self, tmp_path):
        code = "# comment\n\nx = 1\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert len(result) == 3
        assert result[0].raw_strs == []
        assert result[1].raw_strs == []
        assert result[2].raw_strs == ["x", "=", "1"]

    def test_strip_comments_multiple_comments_in_line(self, tmp_path):
        code = "# first\nx = 1  # second\ny = 2 # third\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert len(result) == 3
        assert result[0].raw_strs == []
        assert result[1].raw_strs == ["x", "=", "1"]
        assert result[2].raw_strs == ["y", "=", "2"]

    def test_strip_comments_indentation_preserved(self, tmp_path):
        code = "def f():\n    # indented comment\n    x = 1\n"
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert len(result) == 3
        assert result[0].raw_strs == ["def", "f", "(", ")", ":"]
        assert result[1].indent == 1
        assert result[1].raw_strs == []
        assert result[2].indent == 1
        assert result[2].raw_strs == ["x", "=", "1"]

    def test_strip_comments_does_not_affect_strings(self, tmp_path):
        code = 'x = "# not a comment"\n'
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert result[0].raw_strs == ["x", "=", '"# not a comment"']

    def test_strip_comments_does_not_affect_multiline_strings(self, tmp_path):
        code = '''x = """# inside triple quotes"""\n'''
        file = write_temp_file(tmp_path, code)
        result = RawLineBuilder.read_file_to_tokens(file, strip_comments=True)
        assert result[0].raw_strs == ["x", "=", '"""', "# inside triple quotes", '"""']
