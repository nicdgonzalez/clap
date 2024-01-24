from __future__ import annotations

import sys
from os import path
from typing import TYPE_CHECKING

from .core import CommandBase

if TYPE_CHECKING:
    from builtins import list as List
    from typing import Callable, Optional, Self

# fmt: off
__all__ = (
    "ArgumentParser",
)
# fmt: on


class Extension:
    def __new__(cls) -> Self:
        this = super().__new__(cls)
        # Accumulate commands...
        return this


class ArgumentParser(CommandBase[int]):
    def __init__(
        self,
        brief: str,
        *,
        description: Optional[str] = None,
        epilog: Optional[str] = None,
        program: str = path.basename(sys.argv[0]),
    ) -> None:
        self._brief = brief
        self._description = description
        self._epilog = epilog
        self._program = program
        self._callback: Optional[Callable[..., int]] = None

    @property
    def name(self) -> str:
        return self._program

    @property
    def callback(self) -> Optional[Callable[..., int]]:
        return self._callback

    def __call__(
        self, raw_args: List[str] = sys.argv, /, help_fmt: object = object()
    ) -> int:
        return 0

    def main(self, callback: Callable[..., int], /) -> None:
        if len(self.commands) > 0:
            raise RuntimeError(
                "Is this a CLI tool or a script? "
                "Can't set `main` if you are using commands!"
            )

        self._callback = callback
        return self._callback
