# Overview

**Clap** is a simple and easy-to-use command-line argument parser. Write less
boilerplate code by letting Clap generate everything for you based on function
signatures and documentation.

There is a catch: you need to be writing documentation! The more documentation
you add to your code, the better your command-line interface will be. But don't
worry—all documentation is optional, Clap doesn't hold it against you
(which is nice for prototyping); obviously, however, that means you will end up
with a very bare-bones help message.

## Installation

**Requires Python 3.13+.**

Install this project using pip:

```bash
python3 -m pip install --upgrade git+https://github.com/nicdgonzalez/clap.git
```

### Quickstart

For applications with only a single command, use the `@clap.script` decorator.

```python
from typing import Annotated

import clap


@clap.script()
def main(
    # Positional arguments become positional-only command-line arguments.
    minimum: Annotated[int, clap.Rename("min")],
    maximum: Annotated[int, clap.Rename("max")],
    *,
    # Keyword-only arguments become command-line options.
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
    pass  # Implementation is in the `examples` directory.


if __name__ == "__main__":
    main.run()
    # The `Script` object is just a wrapper over the function. You can still
    # use it same as before:
    # main(minimum=1, maximum=1000, skip_empty=True)
```

The default generated help message:

> [!TIP]
> Although currently undocumented, the help message format is customizable.

```console
$ python3 ./examples/fizzbuzz.py --help
An implementation of FizzBuzz to demonstrate clap!

FizzBuzz is a simple programming task where you iterate over a range of values
and print either "Fizz" or "Buzz" if the index is divisible by 3 or 5
(respectively). If the index is divisible by both, print "FizzBuzz".

Usage: fizzbuzz.py <min> <max>

Arguments:
  min  The index to start from (inclusive)
  max  The index to stop at (inclusive)

Options:
  -s, --skip-empty  Skip indices that don't print anything
  -h, --help        Display this help message and exit
```

TODO: Show examples for `Application` and `Application`+`Extension`. (For now,
see the [examples](./examples) directory.)

## Limitations

Currently, this library only supports NumPy style docstrings. I recognize that
this may limit some users who prefer different documentation styles. If you
have experience with other docstring formats and would like to help, please
consider contributing!
