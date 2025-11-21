"""
This module contains my working test code.

This currently runs to completion successfully.
"""

import dataclasses
from typing import Annotated

import clap
from clap import Long, Short


@dataclasses.dataclass
class Parser(clap.ArgumentParser):
    verbose: Annotated[bool, Long, Short]
    timeout: int = 1000


def main() -> None:
    args = Parser.try_parse(["--verbose", "500"])
    assert args.verbose, args.verbose
    assert args.timeout == 500, args.timeout


if __name__ == "__main__":
    main()
