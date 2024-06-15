from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from typing_extensions import Self


class Alias(str):

    def __new__(cls, value: str) -> Self:
        if len(value) > 1:
            raise ValueError("value must be a single character")

        return super().__new__(cls, value)


class Range:

    def __init__(self, minimum: int, /, maximum: Optional[int] = None) -> None:
        if maximum is not None:
            minimum, maximum = sorted((minimum, maximum))

        self._minimum = minimum
        self._maximum = maximum if maximum is not None else minimum

    @property
    def minimum(self) -> int:
        return self._minimum

    @property
    def maximum(self) -> int:
        return self._maximum


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
