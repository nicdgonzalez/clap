from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, TypeVar

from .abc import PositionalArgument
from .metadata import Range
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import type as Type
    from typing import Any, Self, Union

# fmt: off
__all__ = (
    "Positional",
)
# fmt: on

T = TypeVar("T")


class Positional(PositionalArgument[T]):
    def __init__(
        self,
        *,
        name: str,
        brief: str,
        target_type: Type[T],
        default_value: T = MISSING,
        n_args: Union[Range, int] = Range(0, 1),
    ) -> None:
        self._name = name
        self._brief = brief
        self._target_type = target_type
        self._default_value = default_value

        if isinstance(n_args, int):
            n_args = Range(n_args, n_args)

        self.n_args = n_args

    @classmethod
    def from_parameter(cls, parameter: inspect.Parameter) -> Self:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def target_type(self) -> Type[T]:
        return self._target_type

    @property
    def default_value(self) -> T:
        return self._default_value
