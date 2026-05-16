from pathlib import Path

from .file_parser import FileParser
from .ir_builder import IRBuilder
from .ir_builder_dt import IRFile


def build_python_file(
    path: Path,
    strip_comments: bool = False,
) -> IRFile:
    """Функция сборки IR представления файла"""
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"Ожидался файл, но путь ведёт к директории: {path}")

    return IRBuilder.build(FileParser.parse(path, strip_comments), path)


def build_python_files_dir(
    path: Path,
    strip_comments: bool = False,
) -> dict[str, IRFile]:
    """Функция сборки IR представления директории"""
    if not path.exists():
        raise FileNotFoundError(f"Директория не найдена: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Ожидалась директория, но путь ведёт к файлу: {path}")

    result = {}
    for file in path.rglob("*.py"):
        result[file.relative_to(path).as_posix()] = IRBuilder.build(
            FileParser.parse(file, strip_comments),
            path,
        )

    for file in path.rglob("*.pyi"):
        result[file.relative_to(path).as_posix()] = IRBuilder.build(
            FileParser.parse(file, strip_comments),
            path,
        )

    if not result:
        raise ValueError(f"В директории {path} не найдено .py или .pyi файлов")

    return result
