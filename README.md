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

[Introduction](#introduction)
| [Installation](#installation)
| [Quickstart](#quickstart)
| [Acknowledgements](#acknowledgements)

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
> This library currently only supports parsing through docstrings that
> follow the [NumPy documentation format](https://github.com/numpy/numpydoc).

<a name="script"></a>
### Script

The Script interface is useful for times when you only need to expose a single
function to the command line. For exposing multiple functions, see the
[Application](#application) section.

The following is a minimized example to give you an idea of what this project
looks like. See the [examples](./examples/) directory for the full code
and additional examples!

```python
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

    FizzBuzz is a simple programming task where [...]

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


if __name__ == "__main__":
    formatter = clap.HelpFormatter(...)
    _ = clap.parse_args(fizzbuzz, formatter=formatter)
```

```console
$ python ./examples/fizzbuzz.py --help
A simple FizzBuzz implementation demonstrating clap.Script!

DESCRIPTION:
  FizzBuzz is a simple programming task where you iterate over a range of values
  and print either "Fizz" or "Buzz" when the index is divisible by `3` or `5`
  (respectively). If the index is divisible by both values, print both (i.e.
  "FizzBuzz").

USAGE:
  fizzbuzz.py [--help | --skip-empty] [min=1] [max=15]

OPTIONS:
  -h, --help        Shows this help message and exits
  -s, --skip-empty  Whether to skip indexes that don't print anything

ARGUMENTS:
  min  The index to start from (inclusive) [default: 1]
  max  The index to stop at (inclusive) [default: 15]
```

<a name="application"></a>
### Application

The Application interface is useful for times when you need to expose multiple
functions to the command line. For exposing a single function, see the
[Script](#script) section.

The following is a minimized example to give you an idea of what this project
looks like. See the [examples](./examples/) directory for the full code
and additional examples!

> [!TIP]
> Check out [Fuji](https://github.com/nicdgonzalez/fuji) for a more robust
> example of the application interface.

```python
import dataclasses

import clap

app = clap.Application(
    brief="A simple to-do application demonstrating clap.Application!"
)


@dataclasses.dataclass
class Task:
    id: int
    note: str
    is_complete: bool


@app.command(name="list", aliases=["ls"])
def list_command(*, all: bool = False):
    """Display all of the available tasks.

    Parameters
    ----------
    all : bool
        Whether to also display completed tasks.
    """


@app.command()
def add(note: str):
    """Create a new task.

    Parameters
    ----------
    note : str
        A message representing the task to be completed.
    """


@app.command()
def delete(id: int):
    """Remove an existing task.

    Parameters
    ----------
    id : int
        The unique identifier of an existing task.
    """


if __name__ == "__main__":
    clap.parse_args(app)
```

```console
$ python ./examples/to_do.py --help
A simple to-do application demonstrating clap.Application!

USAGE:
  to-do [--help] <command> [<args>...]

OPTIONS:
  -h, --help  Shows this help message and exits

COMMANDS:
  list         Display all of the available tasks.
  add          Create a new task.
  delete       Remove an existing task.

Built using ndg.clap!
```

<a name="acknowledgements"></a>
## Acknowledgements

The Application and Extension interface (not shown in the above
examples, but used in the Fuji project mentioned) is heavily
inspired by [rapptz/discord.py](https://github.com/rapptz/discord.py)'s
Bot and Cog implementation. discord.py is one of the most well-written
Python libraries out there. Thank you for sharing this masterpiece with
the open source community, and enabling me to create something I think
can be useful to others!
