"""
This module contains my working test code.

This currently runs to completion successfully.
"""

from typing import Annotated

import clap
from clap import Count, Flatten, Long, Short


class Verbosity:
    verbose: Annotated[int, Count, Long, Short] = 0
    quiet: Annotated[int, Count, Long, Short] = 0


class Parser(
    clap.ArgumentParser,
    version="0.1.0",
    about="Converts Windows' animated cursors to Linux.",
    long_about="...",
    after_help="Repository: https://github.com/nicdgonzalez/clap",
):
    # verbosity: Annotated[Verbosity, Flatten]
    verbose: Annotated[bool, Long, Short] = False
    silent: Annotated[bool, Long, Short] = False
    timeout: int = 1000


def main() -> None:
    args = Parser.try_parse(["--verbose", "-q", "500"])
    assert args.verbose is True, args.verbose
    assert args.quiet is True, args.quiet
    assert args.timeout == 500, args.timeout


if __name__ == "__main__":
    main()
