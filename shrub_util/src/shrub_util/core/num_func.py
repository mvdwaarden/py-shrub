import math

REBASE_LOOKUP = "0123456789abcdefghijklmnopqrstuvwxyz"


def num_decimal_rebase(x: int, base: int) -> str:
    exponents = []
    t = x
    e = math.floor(math.log(t, base))
    while e >= 0:
        e_val = math.pow(base, e)
        val = math.floor(t / e_val)
        t -= e_val * val
        exponents.append(REBASE_LOOKUP[val])
        e -= 1
    return "".join(exponents)


def num_rebased_decimal_str_to_decimal(rebased_decimal_str: str, base: int) -> int:
    x = 0
    e = len(rebased_decimal_str) - 1
    for c in rebased_decimal_str:
        e_val = math.pow(base, e)
        idx = REBASE_LOOKUP.find(c)
        x += idx * e_val
        e -= 1
    return int(x)


def test_num_rebase_test_to_bin():
    x = 1000
    print(num_decimal_rebase(x, 16))


if __name__ == "__main__":
    test_num_rebase_test_to_bin()

    for i in range(2, 26):
        rebased = num_decimal_rebase(2024, i)
        print(
            f"base {i} : {rebased} (check:{num_rebased_decimal_str_to_decimal(rebased, i)})"
        )
