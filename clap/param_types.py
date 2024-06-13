from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from .abc import ParameterizedArgument
from .annotations import Alias, Conflicts, Range, Requires
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import set as Set
    from builtins import tuple as Tuple
    from builtins import type as Type
    from typing import Any, Optional

    T = TypeVar("T")

__all__ = ("Positional", "Option")


class Positional(ParameterizedArgument):

    def __init__(
        self,
        name: str,
        brief: str,
        *,
        target_type: Type[T],
        default: T = MISSING,
        n_args: Tuple[int, int] = (0, 1),
    ) -> None:
        self._name = name
        self._brief = brief

        self._target_type = target_type

        # `default` can be MISSING since `None` is a valid value
        if default is not MISSING and not isinstance(default, target_type):
            raise TypeError("default must be an instance of target_type")
        else:
            self._default = default

        if len(n_args) == 1:
            n_args = (n_args[0], n_args[0])
        elif 1 > len(n_args) > 2:
            raise ValueError(
                "n_args expected 1 or 2 values, got {}".format(len(n_args))
            )

        self._n_args = Range(*sorted(n_args))

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
    def default(self) -> Any:
        return self._default

    @property
    def n_args(self) -> Range:
        return self._n_args


# NOTE: I am aware that `Option` is largely an extension of `Positional`.
# I opted to keep them separate as I can not confidently say I will not
# violate the Liskov substitution principle...
# https://en.wikipedia.org/wiki/Liskov_substitution_principle


class Option(ParameterizedArgument):

    def __init__(
        self,
        name: str,
        brief: str,
        *,
        target_type: Type[T],
        default: T = MISSING,
        n_args: Tuple[int, int] = (0, 1),
        alias: str = "",
        requires: Optional[Set[str]] = None,
        conflicts: Optional[Set[str]] = None,
    ) -> None:
        self._name = name
        self._brief = brief

        self._target_type = target_type

        # `default` can be MISSING since `None` is a valid value
        if default is not MISSING and not isinstance(default, target_type):
            raise TypeError("default must be an instance of target_type")
        else:
            self._default = default

        if len(n_args) == 1:
            n_args = (n_args[0], n_args[0])
        elif 1 > len(n_args) > 2:
            raise ValueError(
                "n_args expected 1 or 2 values, got {}".format(len(n_args))
            )

        self._n_args = Range(*sorted(n_args))

        if len(alias) > 1:
            raise ValueError("option alias must be a single character or None")

        self._alias = Alias(alias)
        self._requires = Requires(*requires or set())
        self._conflicts = Conflicts(*conflicts or set())

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
    def default(self) -> Any:
        return self._default

    @property
    def n_args(self) -> Range:
        return self._n_args

    @property
    def alias(self) -> str:
        return self._alias

    @property
    def requires(self) -> Requires[str]:
        return self._requires

    @property
    def conflicts(self) -> Conflicts[str]:
        return self._conflicts
