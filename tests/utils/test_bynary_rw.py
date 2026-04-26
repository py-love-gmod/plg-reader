import math
from io import BytesIO
from pathlib import Path

import pytest

from plg_reader._utils import BinaryRW


class TestBinaryRW:
    @staticmethod
    def roundtrip(obj, header="", file=None):
        """Универсальный roundtrip: возвращает (header, payload) или (payload,) если file передан."""
        if file is None:
            f = BytesIO()
            BinaryRW.dump(f, header, obj)
            f.seek(0)
            return BinaryRW.load(f)

        else:
            BinaryRW.dump(file, header, obj)
            file.seek(0)
            return BinaryRW.load(file)

    # простые типы
    def test_none(self):
        _, p = self.roundtrip(None)
        assert p is None

    def test_bool(self):
        for val in (True, False):
            _, p = self.roundtrip(val)
            assert p is val

    def test_int_positive(self):
        for value in (0, 1, 127, 128, 16383, 16384, 2**20, 2**64 - 1, 10**100):
            _, p = self.roundtrip(value)
            assert p == value

    def test_int_negative(self):
        for value in (-1, -42, -127, -128, -16383, -16384, -(10**100)):
            _, p = self.roundtrip(value)
            assert p == value

    def test_float(self):
        for value in (
            0.0,
            1.0,
            -1.5,
            3.14159,
            float("inf"),
            float("-inf"),
            float("nan"),
        ):
            _, p = self.roundtrip(value)
            if math.isnan(value):
                assert math.isnan(p)
            else:
                assert p == value

    def test_str(self):
        for value in ("", "hello", "привет 🐍", "x" * 1000):
            _, p = self.roundtrip(value)
            assert p == value

    def test_bytes(self):
        for value in (b"", b"\x00\x01\x02", b"hello", bytes(range(256))):
            _, p = self.roundtrip(value)
            assert p == value

    # контейнеры
    def test_list(self):
        obj = [1, 2.5, "three", None, [4, 5]]
        _, p = self.roundtrip(obj)
        assert p == obj

    def test_empty_list(self):
        _, p = self.roundtrip([])
        assert p == []

    def test_tuple(self):
        obj = (1, "a", (2, 3))
        _, p = self.roundtrip(obj)
        assert p == obj

    def test_empty_tuple(self):
        _, p = self.roundtrip(())
        assert p == ()

    # dict с разнородными ключами
    def test_dict(self):
        obj = {"a": 1, "b": 2.5, "c": None, "d": [1, 2]}
        _, p = self.roundtrip(obj)
        assert p == obj

    def test_empty_dict(self):
        _, p = self.roundtrip({})
        assert p == {}

    def test_dict_mixed_keys(self):
        obj = {
            1: "int key",
            (2, 3): "tuple key",
            None: "none key",
            False: "bool key",
            "str": "string key",
            # float ключ – ок, но сравнение может быть неточным, используем 1.0
            1.0: "float key",  # noqa: F601
        }
        _, p = self.roundtrip(obj)
        # float 1.0 и int 1 считаются одинаковыми ключами в Python, но после roundtrip
        # должно остаться так же. Проверяем, что ключи совпадают.
        assert len(p) == len(obj)
        for k, v in obj.items():
            assert k in p
            assert p[k] == v

    def test_dict_bytes_key(self):
        """Bytes ключи допустимы, хотя и необычны."""
        obj = {b"binary": 42}
        _, p = self.roundtrip(obj)
        assert p == obj

    # set
    def test_set(self):
        obj = {1, 2.5, "three", None}
        _, p = self.roundtrip(obj)
        assert p == obj

    def test_empty_set(self):
        _, p = self.roundtrip(set())
        assert p == set()

    def test_set_nested(self):
        # frozenset не сериализуется, поэтому проверим, что внутри set можно хранить только поддерживаемые типы
        with pytest.raises(TypeError):
            self.roundtrip({frozenset([1])})

    # вложенные структуры
    def test_complex_structure(self):
        obj = [
            {"id": 42, "values": (1, 2, 3), "flag": True, "tags": {1, 2, 3}},
            [None, b"data", "text"],
            (4, 5, {"nested": "yes", "nums": {-1, -2}}),
        ]
        _, p = self.roundtrip(obj)
        assert p == obj

    def test_nested_empty_containers(self):
        obj = ([], (), {}, set(), {"empty_list": [], "empty_dict": {}})
        _, p = self.roundtrip(obj)
        assert p == obj

    # заголовок
    def test_header_preserved(self):
        header = "my header"
        obj = {"key": [1, 2, 3]}
        h, p = self.roundtrip(obj, header)
        assert h == header
        assert p == obj

    def test_empty_header(self):
        h, p = self.roundtrip(42, "")
        assert h == ""
        assert p == 42

    def test_unicode_header(self):
        header = "строка こんにちは 🚀"
        obj = [1, 2, 3]
        h, p = self.roundtrip(obj, header)
        assert h == header
        assert p == obj

    # ошибки
    def test_unsupported_type(self):
        with pytest.raises(TypeError, match="Unsupported type"):
            BinaryRW.dump(BytesIO(), "", object())

    def test_unknown_tag(self):
        f = BytesIO(b"\xff")
        with pytest.raises(ValueError, match="Unknown tag"):
            BinaryRW._read_obj(f)

    def test_invalid_magic(self):
        f = BytesIO(b"BADD")
        with pytest.raises(ValueError, match="Invalid magic"):
            BinaryRW.load(f)

    # запись в реальный файл
    def test_real_file(self, tmp_path: Path):
        file_path = tmp_path / "test.plg"
        obj = {"real": [1, 2.5, "file"]}
        header = "hi"
        with open(file_path, "wb") as f:
            BinaryRW.dump(f, header, obj)

        with open(file_path, "rb") as f:
            h, p = BinaryRW.load(f)

        assert h == header
        assert p == obj
