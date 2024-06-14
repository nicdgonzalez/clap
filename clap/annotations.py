from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


class Alias:

    def __init__(self, value: str, /) -> None:
        if len(value) > 1:
            raise ValueError("value must be a single character")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str, /) -> None:
        if len(value) > 1:
            raise ValueError("value must be a single character")

        self._value = value


class Range:

    def __init__(self, minimum: int, /, maximum: Optional[int] = None) -> None:
        if maximum is not None:
            minimum, maximum = sorted((minimum, maximum))

        self._minimum = minimum
        self._maximum = maximum if maximum is not None else minimum


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
