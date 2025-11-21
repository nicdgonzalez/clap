"""
I started with how I wanted the library to work, then started writing.

What you see here is not what the library is currently able to do, but rather
it is the end goal.
"""

import dataclasses
import enum
import os
import pathlib
import sys
from typing import Annotated

import clap
from clap.prelude import *


@dataclasses.dataclass
class Format(clap.Args):
    # Positional-only arguments
    sources: Annotated[pathlib.Path, Nargs(1, ...)]


class Subcommand(clap.Subcommand):
    # new: New
    # init: Init
    # build: Build
    # check: Check
    format: Format


class Parser(
    clap.ArgumentParser,
    # Program name
    program=os.path.basename(sys.argv[0]),
    # Adds flags `-V` and `--version`.
    version="0.1.0",  # str | None
    # Adds flags `-h` and `--help`.
    help=True,
    # Briefly explains what the program does.
    about="Converts Windows' animated cursors to Linux.",
    # Space to explain the program in more detail.
    long_about="...",
    # Additional information that appears after the options.
    after_help="Repository: https://github.com/nicdgonzalez/clap",
):
    verbose: Annotated[
        int,
        Action.COUNT,
        Long,
        Short,
        Global(True),  # Can also be matched on any subcommand.
        Help("Use verbose output (or `-vv` for more verbose output)"),
    ] = 0
    quiet: Annotated[
        int,
        Action.COUNT,
        Long,
        Short,
        Global(True),
        Help("Use quiet output (or `-qq` to silence all output)"),
    ] = 0
    minimum: Annotated[int, Long, Short, Rename("min")] = 0
    maximum: Annotated[int, Long, Short, Rename("max")] = 0
    config: Annotated[pathlib.Path, Long, Short] = pathlib.Path.cwd().joinpath(
        "pyproject.toml"
    )

    # Positional-only arguments
    subcommand: Subcommand


def main() -> None:
    args: Parser = Parser.parse()  # `sys.exit(2)` on failure.
    # args = MyParser.try_parse()  # `raise ArgumentError(...)` on failure.

    result = handle_subcommand(args.subcommand)
