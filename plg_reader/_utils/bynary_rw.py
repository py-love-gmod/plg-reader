import struct


class BinaryRW:
    @staticmethod
    def _write_varint(f, value):
        while value >= 0x80:
            f.write(struct.pack("<B", (value & 0x7F) | 0x80))
            value >>= 7

        f.write(struct.pack("<B", value))

    @staticmethod
    def _read_varint(f):
        value = 0
        shift = 0
        while True:
            b = f.read(1)[0]
            value |= (b & 0x7F) << shift
            shift += 7
            if not (b & 0x80):
                break

        return value

    @staticmethod
    def dump(obj, file):
        BinaryRW._write_obj(file, obj)

    @staticmethod
    def load(file):
        return BinaryRW._read_obj(file)

    @staticmethod
    def _write_obj(f, obj):
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
                b = obj.encode("utf-8")
                f.write(b"\x04")
                BinaryRW._write_varint(f, len(b))
                f.write(b)

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

    @staticmethod
    def _read_obj(f):
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
                s = set()
                for _ in range(size):
                    s.add(BinaryRW._read_obj(f))

                return s

            case _:
                raise ValueError(f"Unknown tag: {tag}")
