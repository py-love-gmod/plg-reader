import pytest

from plg_reader import build_python_file, build_python_files_dir


def test_file_not_found(tmp_path):
    bad = tmp_path / "notthere.py"
    with pytest.raises(FileNotFoundError, match="Файл не найден"):
        build_python_file(bad)


def test_path_is_directory(tmp_path):
    with pytest.raises(IsADirectoryError, match="Ожидался файл"):
        build_python_file(tmp_path)


def test_dir_not_found(tmp_path):
    """Несуществующая директория -> FileNotFoundError"""
    bad = tmp_path / "nodir"
    with pytest.raises(FileNotFoundError, match="Директория не найдена"):
        build_python_files_dir(bad)


def test_build_dir_path_is_file(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x = 1")
    with pytest.raises(NotADirectoryError, match="Ожидалась директория"):
        build_python_files_dir(f)


def test_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="Нет .py/.pyi файлов"):
        build_python_files_dir(tmp_path)


def test_single_file(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("import os\n")
    result = build_python_files_dir(tmp_path)
    assert isinstance(result, dict)
    assert "mod.py" in result


def test_two_files(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 2\n")
    result = build_python_files_dir(tmp_path)
    assert len(result) == 2
    assert "a.py" in result and "b.py" in result


def test_files_in_subdirs(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.py").write_text("a = 1\n")
    (tmp_path / "root.py").write_text("b = 2\n")
    result = build_python_files_dir(tmp_path)
    assert "root.py" in result
    assert "sub/nested.py" in result
