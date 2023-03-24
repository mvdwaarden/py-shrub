from shrub_util.core.str_func import (
    MaxSizeExceededException,
    StringAppendBuffer,
    str_to_json,
    strip_leading_chars,
    strip_trailing_chars,
)


def test_strip_leading_chars_all():
    assert strip_leading_chars("0000000", "0") == ""


def test_strip_leading_chars_some():
    assert strip_leading_chars("000123", "0") == "123"


def test_strip_leading_chars_some_multi():
    assert strip_leading_chars("09.0004923", "0.9") == "4923"


def test_strip_leading_chars_none():
    assert strip_leading_chars("109.0004923", "0.9") == "109.0004923"


def test_strip_trailing_chars_all():
    assert strip_trailing_chars("0000000", "0") == ""


def test_strip_trailing_chars_some():
    assert strip_trailing_chars("000123", "23") == "0001"


def test_str_to_json():
    value = "	"
    test = ""
    for i in range(1, len(value) + 1):
        test += f"\\u{i:04d}"
    assert str_to_json(value) == test


def test_strip_trailing_chars_some_multi():
    assert strip_trailing_chars("09.0004923", "04329") == "09."


def test_strip_trailing_chars_none():
    assert strip_trailing_chars("09.00049235", "04329") == "09.00049235"


def test_str_to_int():
    assert int("0000123") == 123


def test_string_append_buffer_append():
    sab = StringAppendBuffer(3)

    sab.append("a")
    sab.append("b")
    sab.append("c")
    sab.append("d")
    sab.append("efghijklmnopqrs")
    assert sab.get_value() == "abcdefghijklmnopqrs"


def test_string_append_buffer_strip_end():
    sab = StringAppendBuffer(3)

    sab.append("a")
    sab.append("b")
    sab.append("c")
    sab.append("d")
    sab.append("efghijklmnopqrs")
    sab.append("111110001111")
    sab.strip_trailing_chars("1")
    assert sab.get_value() == "abcdefghijklmnopqrs11111000"


def test_string_append_max_size():
    sab = StringAppendBuffer(3, max_size=10)

    sab.append("a")
    sab.append("b")
    sab.append("c")
    sab.append("d")
    try:
        sab.append("efghijklmnopqrs")
        assert False
    except MaxSizeExceededException as msee:
        assert msee.max_size == 10
        assert msee.new_size == 19


def test_empty_stringbuf():
    sab = StringAppendBuffer(3, max_size=10)

    assert sab.get_value() == "null"


if __name__ == "__main__":
    test_string_append_buffer_append()
    test_string_append_buffer_strip_end()
