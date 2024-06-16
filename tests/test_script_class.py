#!/usr/bin/python

import sys
from typing import Annotated

import clap

script = clap.Script(
    brief="A simple FizzBuzz implementation.",
)


@script.main()
def fizzbuzz(
    *,
    min: int = 1,
    max: int = 100,
    skip_empty: Annotated[bool, clap.Alias("s")] = False,
) -> int:
    """A FizzBuzz implementation to demo the usage of ndg.clap on scripts!

    FizzBuzz is a simple programming task where if a number is divisible by
    X or Y, then you print either "Fizz" or "Buzz". If the number is divisible
    by both, you print both together (i.e. "FizzBuzz").

    Parameters
    ----------
    min: int
        The number to start from
    max: int
        The number to stop at
    skip_empty: bool
        Whether or not to skip all of the empty indexes

    Returns
    -------
    :class:`int` The exit code of the program
    """
    mapping = {
        3: "Fizz",
        5: "Buzz",
    }
    buffer = ""

    start, stop = sorted((min, max))
    index_width = len(str(stop))

    for i in range(start, stop + 1):  # +1 to make the stop argument inclusive
        for n, word in mapping.items():
            if i > 0 and i % n == 0:
                buffer += word

        if skip_empty and buffer == "":
            continue

        print("{0:0>{1}d}: {2}".format(i, index_width, buffer))
        buffer *= 0  # clear the buffer

    return 0


if __name__ == "__main__":
    exit_code = script.parse_args()
    sys.exit(exit_code)
