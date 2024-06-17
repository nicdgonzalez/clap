# Command-line Argument Parser

<a name="introduction"></a>
## Introduction

[![pypi-version](https://badgen.net/pypi/v/ndg.clap)](https://pypi.org/project/ndg.clap)

**ndg.clap** is the command-line argument parser that builds itself.

It is designed to be easy to use by generating all of the boilerplate code
based on function signatures and documentation (i.e. things you should already
be adding to your code anyway).

This project is currently missing a lot of features that you would otherwise get
from the built-in `argparse` library. Though, I plan to cover as much as I can.

[Introduction](#introduction) | [Installation](#installation) | [Quickstart](#quickstart)

<a name="installation"></a>
## Installation

**Python 3.9 or higher is required.**

To install, run the following command(s):

```bash
python -m pip install ndg.clap
```

<a name="quickstart"></a>
## Quickstart

> [!NOTE]
> This library currently only supports parsing through
> [NumPy-style docstrings](https://github.com/numpy/numpydoc).

### Script

<!-- See [examples/fizzbuzz.py](./examples/fizzbuzz.py) for the code. -->

Copy the following code into your own file, then run it using
the `--help` flag!

```python
#!/usr/bin/python

from typing import Annotated

import clap

script = clap.Script(
    # name=...,        # defaults to the filename
    # brief="",        # same as first line of docstring
    # description="",  # same as first paragraph of docstring
    # epilog=...,      # text to display at the end of the help message
)


@script.main()
def fizzbuzz(
    # positional arguments are converted into Positionals
    *,
    # keyword-only arguments are converted into Options
    min: int = 1,
    max: int = 15,
    skip_empty: Annotated[bool, clap.Alias("s")] = False,
) -> None:
    """A simple FizzBuzz implementation to demo `clap.Script`!

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
    script.parse_args(
        # args=[...],  # defaults to sys.argv
        formatter=formatter,
    )
```

```console
$ python ./examples/fizzbuzz.py --help
A simple FizzBuzz implementation to demo `clap.Script`!

DESCRIPTION:
  FizzBuzz is a simple programming task where you iterate over a range of values
  and print either "Fizz" or "Buzz" when the index is divisible by `3` or `5`
  (respectively). If the index is divisible by both values, print both (i.e.
  "FizzBuzz").

USAGE:
  fizzbuzz.py [--help | --min | --max | --skip-empty]

OPTIONS:
  -h, --help        Shows this help message and exits
  --min             The index to start from [default: 1]
  --max             The index to stop at (inclusive) [default: 100]
  -s, --skip-empty  Whether to skip indexes that don't print anything
```

### Application

See the [examples/demo](./examples/demo) directory for the code of this simplified
example.

```console
$ cd ./examples/demo
$ python -m task_app --help
[WORK IN PROGRESS]
```

Also check out [Fuji](https://github.com/nicdgonzalez/fuji) — a full-fledged,
production-ready application built using this project!
