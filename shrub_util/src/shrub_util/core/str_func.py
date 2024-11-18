import json

def strip_leading_chars(value: str, chars_to_strip: str):
    if value is not None:
        idx = 0
        for c in value:
            if c in chars_to_strip:
                idx += 1
            else:
                break

        return value[idx:]

    return value


def strip_trailing_chars(value: str, chars_to_strip: str):
    if value is not None:
        if len(chars_to_strip) == 1:
            while value.endswith(chars_to_strip):
                value = value[:-1]
        else:
            idx = 0
            for c in value[::-1]:
                if c in chars_to_strip:
                    idx += 1
                else:
                    break

            if idx > 0:
                return value[:-idx]

    return value


def str_to_json(value):
    src = (
        "\x5c"
        "\x00\x01\x02\x03\x04\x05\x06\x07"
        "\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        "\x10\x11\x12\x13\x14\x15\x16\x17"
        "\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
        "\x26\x27\x22"
    )
    dest = [
        "\\u005c",
        "\\u0000",
        "\\u0001",
        "\\u0002",
        "\\u0003",
        "\\u0004",
        "\\u0005",
        "\\u0006",
        "\\u0007",
        "\\u0008",
        "\\u0009",
        "\\u000a",
        "\\u000b",
        "\\u000c",
        "\\u000d",
        "\\u000e",
        "\\u000f",
        "\\u0010",
        "\\u0011",
        "\\u0012",
        "\\u0013",
        "\\u0014",
        "\\u0015",
        "\\u0016",
        "\\u0017",
        "\\u0018",
        "\\u0019",
        "\\u001a",
        "\\u001b",
        "\\u001c",
        "\\u001d",
        "\\u001e",
        "\\u001f",
        "\\u0026",
        "\\u0027",
        "\\u0022",
    ]
    for i in range(0, len(dest)):
        value = value.replace(src[i], dest[i])
    return value


def number_to_str_adjective(n: int):
    lookup = {
        0: "zero",
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "nineth",
        10: "tenth",
    }
    return lookup[n % 11]


class MaxSizeExceededException(Exception):
    def __init__(self, max_size, new_size, value):
        super().__init__(
            f"Maximum size {max_size} of StringAppendBuffer reached: " f"{new_size}"
        )
        self.max_size = max_size
        self.new_size = new_size
        self.value = value


class StringAppendBuffer:
    def __init__(self, reserve_size: int = 1000000, encoding="utf-8", max_size=None):
        self.reserve_size = reserve_size
        self.write_pos = 0
        self.buffer = None
        self.encoding = encoding
        self.max_size = max_size

    def append(self, value: str):
        bytes_value = bytes(value, self.encoding)
        new_size = self.write_pos + len(bytes_value)
        if self.max_size is not None and new_size > self.max_size:
            raise MaxSizeExceededException(self.max_size, new_size, self.get_value())
        # reallocate
        if self.buffer is None:
            self.buffer = bytearray(self.reserve_size)
        while len(self.buffer) < new_size:
            self.buffer += bytearray(self.reserve_size)
        self.buffer[self.write_pos : new_size] = bytes_value
        self.write_pos += len(bytes_value)

    def strip_trailing_chars(self, chars_to_strip: str):
        if self.buffer is not None:
            chars_to_strip_bytes = bytes(chars_to_strip, self.encoding)
            while self.write_pos > 0:
                if self.buffer[self.write_pos - 1] == chars_to_strip_bytes[0]:
                    self.write_pos -= 1
                else:
                    break

    def rewind(self, n):
        self.write_pos -= n
        if self.write_pos < 0:
            self.write_pos = 0

    def get_value(self):
        if self.buffer is None:
            return "null"
        result = str(self.buffer[0 : self.write_pos], self.encoding)
        return result


def str_json_encode(value: str) -> str:
    return json.dumps(json.loads(value))