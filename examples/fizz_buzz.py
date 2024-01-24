import sys
from os import path

import clap

parser = clap.ArgumentParser(
    "A demonstration of a dynamic Fizz Buzz implementation.",
)


def fizz_buzz(start: int, stop: int, /) -> None:
    """A demonstration of a dynamic Fizz Buzz implementation.

    Iterate through `range(start, stop)` and for value `i` display Fizz, Buzz,
    or FizzBuzz if `i` is divisible by 3, 5 or both, respectively.

    Parameters
    ----------
    start: :class:`int`
        -
    stop: :class:`int`
        -
    """
    mapping = {
        "Fizz": 3,
        "Buzz": 5,
    }
    buffer = ""

    start, stop = sorted((start, stop))
    stop += 1  # `range(0, 100)` stopping at 99 is unintuitive for FizzBuzz
    index_width = len(str(stop))

    for i in range(start, stop):
        for word, n in mapping.items():
            if i > 0 and i % n == 0:
                buffer += word

        index = str(i).rjust(index_width, "0")
        print(f"{index}: {buffer}")
        buffer *= 0


def main() -> int:
    if len(sys.argv) < 3:
        current_exe = path.basename(sys.argv[0])
        print(f"Usage: {current_exe} <start> <stop>", file=sys.stderr)
        return 1

    _, start, stop, *args = sys.argv

    try:
        start, stop = int(start), int(stop)
    except ValueError as exc:
        raise TypeError("start and stop should both be int values") from exc

    fizz_buzz(start, stop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
