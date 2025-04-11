"""
Clap
====

**Clap** is a simple, easy-to-use command-line argument parser that generates
itself using type annotations and documentation.

Examples
--------
Demonstration for how to write a simple script using clap.
>>> from typing import Annotated
>>>
>>> import clap
>>>
>>>
>>> @clap.script()
>>> def main(
...     # Positional-only arguments convert into `PositionalArgument`s.
...     name: str = "World",
...     *,
...     # Keyword-only parameters convert into `Option`s.
...     count: Annotated[int, clap.Short] = 1,
... ) -> None:
...     \"\"\"Print 'Hello, {name}!' for `count` times.
...
...     Parameters
...     ----------
...     name
...         Who do you want to greet?
...     count
...         How many times do you want to greet them?
...     \"\"\"
...     for _ in range(count):
...         print(f"Hello, {name}!")
>>>
>>>
>>> main.run(input=["--help"])
Print 'Hello, {name}!' for `count` times.

Usage: example.py [options] [--] [name]

Arguments:
  name  Who do you want to greet?

Options:
  -c, --count  How many times do you want to greet them?
  -h, --help   Display this help message and exit
>>> main.run()
Hello, World!
>>> main.run(input=["-c", "3"])
Hello, World!
Hello, World!
Hello, World!
>>> main.run(input=["Nic"])
Hello, Nic!
>>> main.run(input=["--count"])
error: expected value for option 'count'
>>> main.run(input=["Hello", "World"])
error: expected 1 argument, got 2
"""

from .application import Application
from .attributes import MetaVar, Rename, Short
from .decorators import group, script, subcommand
from .extension import Extension
from .help import HelpFormatter

__all__ = (
    "Application",
    "Extension",
    "HelpFormatter",
    "MetaVar",
    "Rename",
    "Short",
    "group",
    "script",
    "subcommand",
)
