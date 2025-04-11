"""
A simple script to demonstrate the `clap.script` decorator.
"""

from typing import Annotated

import clap


@clap.script()
def main(
    minimum: Annotated[int, clap.Rename("min")],
    maximum: Annotated[int, clap.Rename("max")],
    *,
    skip_empty: Annotated[bool, clap.Short] = False,
) -> None:
    """An implementation of FizzBuzz to demonstrate clap!

    FizzBuzz is a simple programming task where you iterate over a range of
    values and print either "Fizz" or "Buzz" if the index is divisible by
    3 or 5 (respectively). If the index is divisible by both, print "FizzBuzz".

    Parameters
    ----------
    minimum
        The index to start from (inclusive).
    maximum
        The index to stop at (inclusive).

    Other Parameters
    ----------------
    skip_empty
        Skip indices that don't print anything.
    """
    mapping = {
        3: "Fizz",
        5: "Buzz",
    }
    buffer = ""

    start, stop = sorted((minimum, maximum))
    index_width = len(str(stop))  # To align the number column when printing.

    for i in range(start=start, stop=stop + 1, step=1):
        for n, fizzbuzz in mapping.items():
            if i > 0 and i % n == 0:
                buffer += fizzbuzz

        if skip_empty and buffer == "":
            continue

        print(f"{i:0>{index_width}d}: {buffer}")
        buffer = ""


if __name__ == "__main__":
    main.run()
