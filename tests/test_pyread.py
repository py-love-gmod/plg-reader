import pytest

from plg_reader._python_reader.text_to_tokens import PyRead


def write_temp_file(tmp_path, content):
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")
    return file


class TestPyRead:
    def test_simple_assignment(self, tmp_path):
        code = "x = 1\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert len(result) == 1
        assert result[0].intend == 0
        assert result[0].raw_strs == ["x", "=", "1"]

    def test_indented_block(self, tmp_path):
        code = "def foo():\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert len(result) == 2
        assert result[0].intend == 0
        assert result[0].raw_strs == ["def", "foo", "(", ")", ":"]
        assert result[1].intend == 1
        assert result[1].raw_strs == ["pass"]

    def test_tabs_as_indent(self, tmp_path):
        code = "def foo():\n\tpass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[1].intend == 1
        assert result[1].raw_strs == ["pass"]

    def test_mixed_indent_spaces_and_tabs(self, tmp_path):
        code = "def foo():\n \t pass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[1].intend == 1

    def test_multiple_dedent(self, tmp_path):
        code = "if True:\n    if False:\n        pass\n    else:\n        pass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        levels = [line.intend for line in result]
        assert levels == [0, 1, 2, 1, 2]

    def test_empty_lines_ignored(self, tmp_path):
        code = "def foo():\n\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert len(result) == 2

    def test_string_with_spaces(self, tmp_path):
        code = 'x = "hello world"\n'
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", '"', "hello", "world", '"']

    def test_triple_quoted_string(self, tmp_path):
        code = '"""a b c"""\n'
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ['"""', "a", "b", "c", '"""']

    def test_triple_quoted_multiline(self, tmp_path):
        code = '"""line1\nline2"""\n'
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ['"""', "line1"]
        assert result[1].raw_strs == ["line2", '"""']

    def test_implicit_string_concatenation(self, tmp_path):
        code = '" " " " " "\n'
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ['"', '"', '"', '"', '"', '"']

    def test_f_string(self, tmp_path):
        code = 'f"hello {name}"\n'
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ["f", '"', "hello", "{", "name", "}", '"']

    def test_raw_string_correct(self, tmp_path):
        code = r'r"\n"' + "\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ["r", '"', "\\n", '"']

    def test_escape_in_string(self, tmp_path):
        code = r'"\""' + "\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ['"', '\\"', '"']

    def test_comment_handling(self, tmp_path):
        code = "x = 1  # comment\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert "#" in result[0].raw_strs or "comment" in result[0].raw_strs

    def test_line_continuation(self, tmp_path):
        code = "x = 1 + \\\n    2\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert len(result) == 2
        assert result[0].raw_strs == ["x", "=", "1", "+", "\\"]
        assert result[1].raw_strs == ["2"]

    def test_utf8_bom(self, tmp_path):
        code = "x = 1\n"
        file = tmp_path / "test.py"
        file.write_bytes(b"\xef\xbb\xbf" + code.encode("utf-8"))
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ["x", "=", "1"]

    def test_syntax_error_raises(self, tmp_path):
        code = "def foo(\n"
        file = write_temp_file(tmp_path, code)
        with pytest.raises(SyntaxError):
            PyRead.read_file_to_tokens(file)

    def test_operators_and_brackets(self, tmp_path):
        code = "a = (1 + 2) * 3\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ["a", "=", "(", "1", "+", "2", ")", "*", "3"]

    def test_decorator(self, tmp_path):
        code = "@deco\ndef foo():\n    pass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].intend == 0
        assert result[0].raw_strs == ["@", "deco"]

    def test_class_with_method(self, tmp_path):
        code = "class A:\n    def method(self):\n        self.x = 1\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert [line.intend for line in result] == [0, 1, 2]

    def test_async_function(self, tmp_path):
        code = "async def foo():\n    await bar()\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == ["async", "def", "foo", "(", ")", ":"]
        assert result[1].raw_strs == ["await", "bar", "(", ")"]

    def test_match_case(self, tmp_path):
        code = "match x:\n    case 1:\n        pass\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert [line.intend for line in result] == [0, 1, 2]

    def test_type_hints(self, tmp_path):
        code = "def foo(x: int) -> str:\n    return 'a'\n"
        file = write_temp_file(tmp_path, code)
        result = PyRead.read_file_to_tokens(file)
        assert result[0].raw_strs == [
            "def",
            "foo",
            "(",
            "x",
            ":",
            "int",
            ")",
            "->",
            "str",
            ":",
        ]
