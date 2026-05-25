import pytest

from plg_reader import IRFile, build_python_file


@pytest.fixture
def parse_code(tmp_path):
    def _parse(code: str, strip_comments: bool = True) -> IRFile:
        file = tmp_path / "test.py"
        file.write_text(code, encoding="utf-8")
        return build_python_file(file, strip_comments=strip_comments)

    return _parse
