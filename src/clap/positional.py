from typing import Callable

from .abc import SupportsConvert
from .attributes import MetaVar
from .sentinel import MISSING


class PositionalArgument[T](SupportsConvert[T]):
    """Represents a positional-only command-line argument"""

    def __init__(
        self,
        name: str,
        brief: str,
        target_type: Callable[[str], T],
        default_value: T = MISSING,
        metavar: MetaVar | None = None,
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
        return self._brief

    @property
    def target_type(self) -> Callable[[str], T]:
        return self._target_type

    @property
    def default_value(self) -> T:
        return self._default_value
