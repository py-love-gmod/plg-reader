import struct
from typing import Any, BinaryIO

# region BinTags
_BT_NONE = b"\x00"

_BT_BOOL_T = b"\x01"  # True
_BT_BOOL_F = b"\x02"  # False

_BT_INT_P = b"\x03"  # int > 0
_BT_INT_N = b"\x04"  # int < 0

_BT_FLOAT = b"\x05"

_BT_STRING = b"\x06"

_BT_BYTES = b"\x07"

_BT_LIST = b"\x08"

_BT_TUPLE = b"\x09"

_BT_DICT = b"\x0a"

_BT_SET = b"\x0b"
# endregion


# region Var int
def _write_varint(f: BinaryIO, value: int) -> None:
    while value >= 0x80:
        f.write(struct.pack("<B", (value & 0x7F) | 0x80))
        value >>= 7

    f.write(struct.pack("<B", value))


def _read_varint(f: BinaryIO) -> int:
    value = 0
    shift = 0
    while True:
        b = f.read(1)[0]
        value |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break

    return value


# endregion


# region Read Write obj
# Запись произвольного объекта
def _write_obj(f: BinaryIO, obj: Any) -> None:
    match obj:
        case None:
            f.write(_BT_NONE)

        case bool():
            f.write(_BT_BOOL_T if obj else _BT_BOOL_F)

        case int():
            if obj >= 0:
                f.write(_BT_INT_P)
                _write_varint(f, obj)

            else:
                f.write(_BT_INT_N)
                _write_varint(f, -obj)

        case float():
            f.write(_BT_FLOAT)
            f.write(struct.pack("<d", obj))

        case str():
            f.write(_BT_STRING)
            data = obj.encode("utf-8")
            _write_varint(f, len(data))
            f.write(data)

        case bytes():
            f.write(_BT_BYTES)
            _write_varint(f, len(obj))
            f.write(obj)

        case list():
            f.write(_BT_LIST)
            _write_varint(f, len(obj))
            for item in obj:
                _write_obj(f, item)

        case tuple():
            f.write(_BT_TUPLE)
            _write_varint(f, len(obj))
            for item in obj:
                _write_obj(f, item)

        case dict():
            f.write(_BT_DICT)
            _write_varint(f, len(obj))
            for k, v in obj.items():
                _write_obj(f, k)
                _write_obj(f, v)

        case set():
            f.write(_BT_SET)
            _write_varint(f, len(obj))
            for item in obj:
                _write_obj(f, item)

        case _:
            raise TypeError(f"Unsupported type: {type(obj)}")


# Чтение произвольного объекта
def _read_obj(f: BinaryIO) -> Any:
    tag = f.read(1)

    # Спасибо питон за match. А можно его было сделать просто как в C?
    # При этом сверху юзал его по питонячи. МДААААААААААААА
    if tag == _BT_NONE:
        return None

    elif tag == _BT_BOOL_T:
        return True

    elif tag == _BT_BOOL_F:
        return False

    elif tag == _BT_INT_P:
        return _read_varint(f)

    elif tag == _BT_INT_N:
        return -_read_varint(f)

    elif tag == _BT_FLOAT:
        return struct.unpack("<d", f.read(8))[0]

    elif tag == _BT_STRING:
        size = _read_varint(f)
        return f.read(size).decode("utf-8")

    elif tag == _BT_BYTES:
        size = _read_varint(f)
        return f.read(size)

    elif tag == _BT_LIST:
        size = _read_varint(f)
        return [_read_obj(f) for _ in range(size)]

    elif tag == _BT_TUPLE:
        size = _read_varint(f)
        return tuple(_read_obj(f) for _ in range(size))

    elif tag == _BT_DICT:
        size = _read_varint(f)
        d = {}
        for _ in range(size):
            k = _read_obj(f)
            v = _read_obj(f)
            d[k] = v

        return d

    elif tag == _BT_SET:
        size = _read_varint(f)
        return {_read_obj(f) for _ in range(size)}

    # TODO: Добавить произвольное чтение классов

    else:
        raise ValueError(f"Unknown tag: {tag}")


# endregion


class BinaryRW:
    @staticmethod
    def dump(
        file: BinaryIO,
        header: str,
        obj: None | bool | int | float | str | bytes | list | tuple | dict | set,
    ) -> None:
        """
        Сериализовать объект и записать в файл.
        """
        file.write(b"PLGB")
        header_bytes = header.encode("utf-8")
        _write_varint(file, len(header_bytes))
        file.write(header_bytes)
        _write_obj(file, obj)

    @staticmethod
    def load(
        file: BinaryIO,
    ) -> tuple[
        str,
        None | bool | int | float | str | bytes | list | tuple | dict | set,
    ]:
        """
        Возвращает кортеж (header, payload)
        """
        magic = file.read(4)
        if magic != b"PLGB":
            raise ValueError("Invalid magic signature: expected b'PLGB'")

        header_len = _read_varint(file)
        header = file.read(header_len).decode("utf-8")
        payload = _read_obj(file)
        return header, payload
