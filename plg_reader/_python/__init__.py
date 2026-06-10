from concurrent.futures import as_completed
from pathlib import Path

from _utils import get_cpus_and_executor

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

    files = list(path.rglob("*.py")) + list(path.rglob("*.pyi"))
    if not files:
        raise ValueError(f"Нет .py/.pyi файлов в {path}")

    cpus, Executor = get_cpus_and_executor()
    workers = min(cpus, len(files))

    if workers <= 1:
        return {
            f.relative_to(path).as_posix(): build_python_file(f, strip_comments)
            for f in files
        }

    with Executor(max_workers=workers) as executor:
        future_to_file = {
            executor.submit(build_python_file, f, strip_comments): f for f in files
        }
        result = {}
        for future in as_completed(future_to_file):
            f = future_to_file[future]
            result[f.relative_to(path).as_posix()] = future.result()

    return result
