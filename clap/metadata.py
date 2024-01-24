from __future__ import annotations

import sys
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from typing import Optional

__all__ = (
    "Short",
    "Range",
    "Requires",
    "Conflicts",
)


class Short(str):
    def __new__(cls, value: str) -> Short:
        if len(value) != 1:
            raise ValueError("Option alias must be a single character")

        return super().__new__(cls, value)


class Range(NamedTuple):
    minimum: int
    maximum: Optional[int]


if sys.version_info >= (3, 9):
    _Set = set[str]
else:
    _Set = set


class Requires(_Set):
    def __init__(self, *option_names: str) -> None:
        return super().__init__(option_names)


class Conflicts(_Set):
    def __init__(self, *option_names: str) -> None:
        return super().__init__(option_names)
