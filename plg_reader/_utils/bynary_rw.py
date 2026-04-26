import struct
from typing import Any, BinaryIO


class BinaryRW:
    # Varint
    @staticmethod
    def _write_varint(f: BinaryIO, value: int) -> None:
        while value >= 0x80:
            f.write(struct.pack("<B", (value & 0x7F) | 0x80))
            value >>= 7

        f.write(struct.pack("<B", value))

    @staticmethod
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

    # Публичный API
    @staticmethod
    def dump(file: BinaryIO, header: str, obj: Any) -> None:
        """
        Сериализовать объект и записать в файл.
        """
        file.write(b"PLGB")
        header_bytes = header.encode("utf-8")
        BinaryRW._write_varint(file, len(header_bytes))
        file.write(header_bytes)
        BinaryRW._write_obj(file, obj)

    @staticmethod
    def load(file: BinaryIO) -> tuple[str, Any]:
        """
        Возвращает кортеж (header, payload)
        """
        magic = file.read(4)
        if magic != b"PLGB":
            raise ValueError("Invalid magic signature: expected b'PLGB'")

        header_len = BinaryRW._read_varint(file)
        header = file.read(header_len).decode("utf-8")
        payload = BinaryRW._read_obj(file)
        return header, payload

    # Запись произвольного объекта
    @staticmethod
    def _write_obj(f: BinaryIO, obj: Any) -> None:
        match obj:
            case None:
                f.write(b"\x00")

            case bool():
                f.write(b"\x01" + (b"\x01" if obj else b"\x00"))

            case int():
                f.write(b"\x02")
                if obj >= 0:
                    f.write(b"\x00")  # знак +
                    BinaryRW._write_varint(f, obj)

                else:
                    f.write(b"\x01")  # знак -
                    BinaryRW._write_varint(f, -obj)

            case float():
                f.write(b"\x03")
                f.write(struct.pack("<d", obj))

            case str():
                data = obj.encode("utf-8")
                f.write(b"\x04")
                BinaryRW._write_varint(f, len(data))
                f.write(data)

            case bytes():
                f.write(b"\x05")
                BinaryRW._write_varint(f, len(obj))
                f.write(obj)

            case list():
                f.write(b"\x06")
                BinaryRW._write_varint(f, len(obj))
                for item in obj:
                    BinaryRW._write_obj(f, item)

            case tuple():
                f.write(b"\x07")
                BinaryRW._write_varint(f, len(obj))
                for item in obj:
                    BinaryRW._write_obj(f, item)

            case dict():
                f.write(b"\x08")
                BinaryRW._write_varint(f, len(obj))
                for k, v in obj.items():
                    BinaryRW._write_obj(f, k)
                    BinaryRW._write_obj(f, v)

            case set():
                f.write(b"\x09")
                BinaryRW._write_varint(f, len(obj))
                for item in obj:
                    BinaryRW._write_obj(f, item)

            case _:
                raise TypeError(f"Unsupported type: {type(obj)}")

    # Чтение произвольного объекта
    @staticmethod
    def _read_obj(f: BinaryIO) -> Any:
        tag = f.read(1)[0]
        match tag:
            case 0x00:
                return None

            case 0x01:
                return f.read(1)[0] != 0

            case 0x02:
                sign = f.read(1)[0]
                value = BinaryRW._read_varint(f)
                return value if sign == 0 else -value

            case 0x03:
                return struct.unpack("<d", f.read(8))[0]

            case 0x04:
                size = BinaryRW._read_varint(f)
                return f.read(size).decode("utf-8")

            case 0x05:
                size = BinaryRW._read_varint(f)
                return f.read(size)

            case 0x06:
                size = BinaryRW._read_varint(f)
                return [BinaryRW._read_obj(f) for _ in range(size)]

            case 0x07:
                size = BinaryRW._read_varint(f)
                return tuple(BinaryRW._read_obj(f) for _ in range(size))

            case 0x08:
                size = BinaryRW._read_varint(f)
                d = {}
                for _ in range(size):
                    k = BinaryRW._read_obj(f)
                    v = BinaryRW._read_obj(f)
                    d[k] = v

                return d

            case 0x09:
                size = BinaryRW._read_varint(f)
                return {BinaryRW._read_obj(f) for _ in range(size)}

            case _:
                raise ValueError(f"Unknown tag: {tag}")
