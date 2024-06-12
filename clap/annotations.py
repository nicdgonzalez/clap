from __future__ import annotations

import sys
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from typing import Optional

    from typing_extensions import Self


class Alias(str):

    def __new__(cls, value: str) -> Self:
        if len(value) != 1:
            raise ValueError("alias must be a single character")

        return super().__new__(cls, value)


class Range(NamedTuple):
    minimum: int
    maximum: Optional[int]


if sys.version_info >= (3, 9):
    _Set = set[str]
else:
    _Set = set


class Requires(_Set):

    def __init__(self, *options: str) -> None:
        super().__init__(options)


class Conflicts(_Set):

    def __init__(self, *options: str) -> None:
        super().__init__(options)
