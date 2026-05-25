from plg_reader import IRComment, build_python_file


def test_trailing_comment(tmp_path):
    code = "x = 1  # comment"
    file = tmp_path / "test.py"
    file.write_text(code, encoding="utf-8")
    ir = build_python_file(file, strip_comments=False)
    comments = [n for n in ir.walk() if isinstance(n, IRComment)]
    assert len(comments) == 1
    assert "comment" in comments[0].text


def test_comment_stripped(parse_code):
    ir = parse_code("x = 1  # comment", strip_comments=True)
    comments = [n for n in ir.walk() if isinstance(n, IRComment)]
    assert len(comments) == 0
