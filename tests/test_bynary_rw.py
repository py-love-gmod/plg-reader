import math
from io import BytesIO

import pytest

from plg_reader._utils import BinaryRW


class TestBinaryRW:
    def roundtrip(self, obj):
        f = BytesIO()
        BinaryRW.dump(obj, f)
        f.seek(0)
        return BinaryRW.load(f)

    def test_none(self):
        assert self.roundtrip(None) is None

    def test_bool(self):
        assert self.roundtrip(True) is True
        assert self.roundtrip(False) is False

    def test_int_positive(self):
        for value in (0, 1, 127, 128, 16383, 16384, 2**20, 2**64 - 1, 10**100):
            assert self.roundtrip(value) == value

    def test_int_negative(self):
        for value in (-1, -42, -127, -128, -16383, -16384, -(10**100)):
            assert self.roundtrip(value) == value

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
            result = self.roundtrip(value)
            if math.isnan(value):
                assert math.isnan(result)

            else:
                assert result == value

    def test_str(self):
        for value in ("", "hello", "привет 🐍", "x" * 1000):
            assert self.roundtrip(value) == value

    def test_bytes(self):
        for value in (b"", b"\x00\x01\x02", b"hello", bytes(range(256))):
            assert self.roundtrip(value) == value

    def test_list(self):
        obj = [1, 2.5, "three", None, [4, 5]]
        assert self.roundtrip(obj) == obj

    def test_empty_list(self):
        assert self.roundtrip([]) == []

    def test_tuple(self):
        obj = (1, "a", (2, 3))
        assert self.roundtrip(obj) == obj

    def test_empty_tuple(self):
        assert self.roundtrip(()) == ()

    def test_dict(self):
        obj = {"a": 1, "b": 2.5, "c": None, "d": [1, 2]}
        assert self.roundtrip(obj) == obj

    def test_empty_dict(self):
        assert self.roundtrip({}) == {}

    def test_set(self):
        obj = {1, 2.5, "three", None}
        assert self.roundtrip(obj) == obj

    def test_empty_set(self):
        assert self.roundtrip(set()) == set()

    def test_complex_structure(self):
        obj = [
            {"id": 42, "values": (1, 2, 3), "flag": True, "tags": {1, 2, 3}},
            [None, b"data", "text"],
            (4, 5, {"nested": "yes", "nums": {-1, -2}}),
        ]
        assert self.roundtrip(obj) == obj

    def test_unsupported_type(self):
        with pytest.raises(TypeError, match="Unsupported type"):
            BinaryRW.dump(object(), BytesIO())

    def test_unknown_tag(self):
        f = BytesIO(b"\xff")
        with pytest.raises(ValueError, match="Unknown tag"):
            BinaryRW.load(f)
