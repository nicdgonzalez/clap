# Overview

**Clap** is a simple and easy-to-use command-line argument parser. Write less
boilerplate code by letting Clap generate everything for you based on function
signatures and documentation.

## Installation

**Requires Python 3.13+.**

Install this project using pip:

```bash
python3 -m pip install --upgrade git+https://github.com/nicdgonzalez/clap.git
```

### Quickstart

<details>
<summary>Script</summary>

For programs that expose a single command as the main application.

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
    main.parse_args()
    # The `Script` object is just a wrapper over the function. You can still
    # use it same as before:
    # main(minimum=1, maximum=1000, skip_empty=True)
```

The default generated help message:

> 💡 **TIP**
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

</details>

<details>
<summary>Application</summary>

For programs that expose multiple commands under a single application.

TODO: Show examples for `Application` and `Application`+`Extension`. (For now,
see the [examples](./examples) directory.)

</details>

## Limitations

Currently, the library only supports NumPy style docstrings. I understand that
this may limit some users who prefer other documentation styles, so if you have
experience with other formats and would like to help, please consider opening a
pull request!
