# Overview

**Clap** is a simple and easy-to-use command-line argument parser. Write less
boilerplate code by letting Clap generate everything for you based on function
signatures and documentation.

There is a catch: you need to be writing documentation! The more documentation
you add to your code, the better your command-line interface will be. But don't
worry—all documentation is optional, Clap doesn't hold it against you
(which is nice for prototyping); obviously, however, that means you will end up
with a very bare-bones help message.

<!-- Not sure how much of this belongs in the introduction...

Adding type annotations to your code helps catch bugs and improves the overall
quality of your codebase. This library doesn't require you to write anything
extra to make it work; it takes advantage of practices you should *already be
doing*. The only times you need to add anything "Clap-specific" would be for
things outside of the program (e.g., the `-h` short option for `--help`, which
cannot be naturally inferred otherwise); this is something you would have to do
with any other library as well.

This library is designed for developers who use type annotations consistently
throughout their codebase. The more documentation becomes second nature to you,
the easier this library will be to use!

There is a caveat with this approach: it assumes you understand the Python
type system and are using it *properly*. For this, I recommend using tools like
[mypy], a static type checker that analyzes your code to catch type-related
errors.

-->

## Installation

**Requires Python 3.13+.**

Install this project using pip:

```bash
python3 -m pip install --upgrade git+https://github.com/nicdgonzalez/clap.git
```

### Quickstart

For simple, single-command applications, use `@clap.script`:

```python
"""
A simple script to demonstrate the `clap.script` decorator.
"""

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
```

## Limitations

Currently, this library only supports NumPy style docstrings. I recognize that
this may limit some users who prefer different documentation styles. If you
have experience with other docstring formats and would like to help, please
consider contributing!

[mypy]: https://mypy-lang.org/
