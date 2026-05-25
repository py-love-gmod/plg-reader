from pathlib import Path

import pytest

from plg_reader import build_python_file

PYCODE_DIR = Path(__file__).parent / "compile_files"


def collect_test_files():
    return [(f, f.name) for f in sorted(PYCODE_DIR.glob("*.py"))]


@pytest.mark.parametrize(
    "filepath",
    [f for f, _ in collect_test_files()],
    ids=[name for _, name in collect_test_files()],
)
def test_compile_file(filepath):
    ir = build_python_file(filepath, strip_comments=True)
    assert ir is not None
