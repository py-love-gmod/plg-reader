============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-9.0.3, pluggy-1.6.0 -- F:\Desktop\plg\plg-reader\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: F:\Desktop\plg\plg-reader
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0
collecting ... collected 79 items

tests/python/test_file_parser.py::TestSimpleAssignment::test_single_assignment PASSED [  1%]
tests/python/test_file_parser.py::TestSimpleAssignment::test_multiple_assignments PASSED [  2%]
tests/python/test_file_parser.py::TestSimpleAssignment::test_chained_operators PASSED [  3%]
tests/python/test_file_parser.py::TestKeywords::test_common_keywords PASSED [  5%]
tests/python/test_file_parser.py::TestKeywords::test_banned_keyword_raises PASSED [  6%]
tests/python/test_file_parser.py::TestKeywords::test_banned_keyword_indented PASSED [  7%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[123-123] PASSED [  8%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[0x1F-31] PASSED [ 10%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[0b101-5] PASSED [ 11%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[0o77-63] PASSED [ 12%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[3.14-3.14] PASSED [ 13%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[1_000-1000] PASSED [ 15%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[1e3-1000.0] PASSED [ 16%]
tests/python/test_file_parser.py::TestNumbers::test_valid_numbers[1.5e-2-0.015] PASSED [ 17%]
tests/python/test_file_parser.py::TestNumbers::test_complex_numbers_raise PASSED [ 18%]
tests/python/test_file_parser.py::TestNumbers::test_negative_number PASSED [ 20%]
tests/python/test_file_parser.py::TestNumbers::test_number_with_underscores PASSED [ 21%]
tests/python/test_file_parser.py::TestStrings::test_single_quoted PASSED [ 22%]
tests/python/test_file_parser.py::TestStrings::test_double_quoted PASSED [ 24%]
tests/python/test_file_parser.py::TestStrings::test_f_string PASSED      [ 25%]
tests/python/test_file_parser.py::TestStrings::test_raw_string PASSED    [ 26%]
tests/python/test_file_parser.py::TestStrings::test_triple_quoted_single_line PASSED [ 27%]
tests/python/test_file_parser.py::TestStrings::test_triple_with_prefix PASSED [ 29%]
tests/python/test_file_parser.py::TestStrings::test_escaped_quote PASSED [ 30%]
tests/python/test_file_parser.py::TestStrings::test_byte_string PASSED   [ 31%]
tests/python/test_file_parser.py::TestStrings::test_rb_string PASSED     [ 32%]
tests/python/test_file_parser.py::TestStrings::test_f_string_with_expressions PASSED [ 34%]
tests/python/test_file_parser.py::TestMultilineStrings::test_across_lines PASSED [ 35%]
tests/python/test_file_parser.py::TestMultilineStrings::test_with_indent PASSED [ 36%]
tests/python/test_file_parser.py::TestMultilineStrings::test_closing_quote_followed_by_code PASSED [ 37%]
tests/python/test_file_parser.py::TestMultilineStrings::test_multiline_fstring PASSED [ 39%]
tests/python/test_file_parser.py::TestComments::test_full_line_comment PASSED [ 40%]
tests/python/test_file_parser.py::TestComments::test_inline_comment PASSED [ 41%]
tests/python/test_file_parser.py::TestComments::test_strip_comments_option PASSED [ 43%]
tests/python/test_file_parser.py::TestLineContinuation::test_simple PASSED [ 44%]
tests/python/test_file_parser.py::TestLineContinuation::test_with_indent PASSED [ 45%]
tests/python/test_file_parser.py::TestLineContinuation::test_inside_string PASSED [ 46%]
tests/python/test_file_parser.py::TestSemicolon::test_simple_split PASSED [ 48%]
tests/python/test_file_parser.py::TestSemicolon::test_with_comment PASSED [ 49%]
tests/python/test_file_parser.py::TestEmptyLines::test_empty_line PASSED [ 50%]
tests/python/test_file_parser.py::TestEmptyLines::test_blank_line PASSED [ 51%]
tests/python/test_file_parser.py::TestEmptyLines::test_only_comment FAILED [ 53%]
tests/python/test_file_parser.py::TestFileFeatures::test_utf8_bom PASSED [ 54%]
tests/python/test_file_parser.py::TestFileFeatures::test_empty_file PASSED [ 55%]
tests/python/test_file_parser.py::TestOperatorsAndSeparators::test_parentheses_and_comma PASSED [ 56%]
tests/python/test_file_parser.py::TestOperatorsAndSeparators::test_dot_operator PASSED [ 58%]
tests/python/test_file_parser.py::TestOperatorsAndSeparators::test_ellipsis PASSED [ 59%]
tests/python/test_file_parser.py::TestOperatorsAndSeparators::test_compound_operators PASSED [ 60%]
tests/python/test_file_parser.py::TestComplexStructure::test_full_function PASSED [ 62%]
tests/python/test_file_parser.py::TestEdgeCases::test_unary_vs_binary_minus PASSED [ 63%]
tests/python/test_file_parser.py::TestEdgeCases::test_comment_disables_continuation PASSED [ 64%]
tests/python/test_file_parser.py::TestEdgeCases::test_semicolon_no_empty_group PASSED [ 65%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_none PASSED            [ 67%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_bool PASSED            [ 68%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_int_positive PASSED    [ 69%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_int_negative PASSED    [ 70%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_float PASSED           [ 72%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_str PASSED             [ 73%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_bytes PASSED           [ 74%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_list PASSED            [ 75%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_empty_list PASSED      [ 77%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_tuple PASSED           [ 78%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_empty_tuple PASSED     [ 79%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_dict PASSED            [ 81%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_empty_dict PASSED      [ 82%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_dict_mixed_keys PASSED [ 83%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_dict_bytes_key PASSED  [ 84%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_set PASSED             [ 86%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_empty_set PASSED       [ 87%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_set_nested PASSED      [ 88%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_complex_structure PASSED [ 89%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_nested_empty_containers PASSED [ 91%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_header_preserved PASSED [ 92%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_empty_header PASSED    [ 93%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_unicode_header PASSED  [ 94%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_unsupported_type PASSED [ 96%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_unknown_tag PASSED     [ 97%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_invalid_magic PASSED   [ 98%]
tests/utils/test_bynary_rw.py::TestBinaryRW::test_real_file PASSED       [100%]

================================== FAILURES ===================================
______________________ TestEmptyLines.test_only_comment _______________________

self = <tests.python.test_file_parser.TestEmptyLines object at 0x000001E53601A190>
tmp_path = WindowsPath('C:/Users/Cain/tmp/pytest-of-Cain/pytest-99/test_only_comment0')

    def test_only_comment(self, tmp_path):
        lines = FileParser.parse(write_temp_file(tmp_path, "   # just comment\n"))
        assert len(lines[0].tokens) == 1
        assert lines[0].tokens[0].type == TokenType.COMMENT
>       assert lines[0].indent == 0
E       AssertionError: assert 1 == 0
E        +  where 1 = Line(indent=1, line_num=1, tokens=[Token(pos=(1, 3), data='# just comment', type=<TokenType.COMMENT: 11>)]).indent

tests\python\test_file_parser.py:316: AssertionError
=========================== short test summary info ===========================
FAILED tests/python/test_file_parser.py::TestEmptyLines::test_only_comment - AssertionError: assert 1 == 0
 +  where 1 = Line(indent=1, line_num=1, tokens=[Token(pos=(1, 3), data='# just comment', type=<TokenType.COMMENT: 11>)]).indent
======================== 1 failed, 78 passed in 1.74s =========================
