"""
Metadata
========

This module contains helper types for use with `typing.Annotated` to provide
additional information about a command's arguments and options.

Examples
--------
>>> from typing import Annotated
>>>
>>> import clap
>>> from clap.metadata import Short, Conflicts
>>>
>>>
>>> @clap.command(name="start")
... def start(
...     server: str,
...     /,
...     *,
...     verbose: Annotated[bool, Short('v'), Conflicts("quiet")] = False,
...     quiet: Annotated[bool, Short('q'), Conflicts("verbose")] = False,
... ) -> None:
...     \"\"\"Starts the specified server.
...
...     Parameters
...     ----------
...     server : str
...         The name of the server to start.
...     verbose : bool, default=False
...         Whether to print verbose output.
...     quiet : bool, default=False
...         Whether to suppress all output.
...
...     \"\"\"
...     ...

"""
from __future__ import annotations

from typing import NamedTuple

__all__ = (
    "Range",
    "Short",
    "Requires",
    "Conflicts",
)


class Short(str):
    """Represents a short name for an option."""

    def __new__(cls, value: str) -> Short:
        if len(value) != 1:
            raise ValueError("Short name must be a single character.")
        return super().__new__(cls, value)


class Requires(set[str]):
    """Represents the names of options that are required by another option."""

    def __new__(cls, *args: str) -> Requires:
        return super().__new__(cls)

    def __init__(self, *args: str) -> None:
        super().__init__(args)


class Conflicts(set[str]):
    """Represents the names of options that conflict with another option."""

    def __new__(cls, *args: str) -> Conflicts:
        return super().__new__(cls)

    def __init__(self, *args: str) -> None:
        super().__init__(args)


class Range(NamedTuple):
    """Represents a range of values."""

    minimum: int
    maximum: int
