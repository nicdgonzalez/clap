#!/usr/bin/python

from typing import Annotated

import clap


@clap.script()
def fizzbuzz(
    # positional arguments are converted into Positionals
    min: int = 1,
    max: int = 15,
    *,
    # keyword-only arguments are converted into Options
    skip_empty: Annotated[bool, clap.Alias("s")] = False,
) -> None:
    """A simple FizzBuzz implementation demonstrating clap.Script!

    FizzBuzz is a simple programming task where you iterate over a range of
    values and print either "Fizz" or "Buzz" when the index is divisible by
    `3` or `5` (respectively). If the index is divisible by both values,
    print both (i.e. "FizzBuzz").

    Parameters
    ----------
    min : int
        The index to start from (inclusive)
    max : int
        The index to stop at (inclusive)

    Other Parameters
    ----------------
    skip_empty : bool
        Whether to skip indexes that don't print anything
    """
    mapping = {
        3: "Fizz",
        5: "Buzz",
    }
    buffer = ""

    start, stop = sorted((min, max))
    index_width = len(str(stop))

    for i in range(start, stop + 1):  # +1 to make `stop` inclusive
        for n, word in mapping.items():
            if i > 0 and i % n == 0:
                buffer += word

        if skip_empty and buffer == "":
            continue

        print("{0:0>{1}d}: {2}".format(i, index_width, buffer))
        buffer = ""


if __name__ == "__main__":
    formatter = clap.HelpFormatter(
        # width=80,             # columns that the help message uses
        # name_width=...,       # columns that an item name uses [width // 4]
        # indent=2,             # indentation of each item under a section
        # placeholder="[...]",  # displays if name is longer than name_width
        # compact=False,        # flattens unnecessary newlines
    )
    _ = clap.parse_args(
        fizzbuzz,
        # args=[...],  # defaults to sys.argv
        formatter=formatter,
    )
