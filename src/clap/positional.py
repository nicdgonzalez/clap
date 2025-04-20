import pathlib
from typing import Callable

from .abc import SupportsConvert
from .attributes import MetaVar
from .sentinel import MISSING


# TODO: Documentation.
class PositionalArgument[T](SupportsConvert[T]):
    """Represents a positional-only command-line argument"""

    def __init__(
        self,
        name: str,
        brief: str,
        metavar: MetaVar,
        target_type: Callable[[str], T],
        default_value: T = MISSING,
    ) -> None:
        self._name = name
        self._brief = brief
        self._target_type = target_type
        self._default_value = default_value
        self.metavar = metavar or self.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        if self._target_type is bool or self._default_value is MISSING:
            return self._brief

        default: str
        match self._default_value:
            case pathlib.Path():
                # fmt: off
                default = (
                    self._default_value
                    .as_posix()
                    .replace(pathlib.Path.cwd().as_posix(), ".")
                )
                # fmt: on
            case _:
                default = str(self._default_value)

        return self._brief + f" [{default}]"

    @property
    def target_type(self) -> Callable[[str], T]:
        return self._target_type

    @property
    def default_value(self) -> T:
        return self._default_value
