from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, TypeVar, get_origin

from .abc import ParameterizedArgument
from .annotations import Alias, Conflicts, Range, Requires
from .help import HelpInfo
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import set as Set
    from builtins import tuple as Tuple
    from builtins import type as Type
    from typing import Any, Optional

    from typing_extensions import Self

    T = TypeVar("T")

__all__ = ("Positional", "Option")


def convert_metadata(metadata: Tuple[Any, ...], /) -> Dict[str, Any]:
    type_to_kwarg_map = {
        Range: "n_args",
        Alias: "alias",
        Requires: "requires",
        Conflicts: "conflicts",
    }
    data: Dict[str, Any] = {}

    for value in metadata:
        try:
            key = type_to_kwarg_map[type(value)]
        except KeyError:
            continue  # ignore any unknown metadata

        data[key] = value

    return data


class Positional(ParameterizedArgument):

    def __init__(
        self,
        name: str,
        brief: str,
        *,
        target_type: Type[T],
        default: T = MISSING,
        n_args: Tuple[int, int] = (0, 1),
        **kwargs: Any,
    ) -> None:
        self._name = name
        self._brief = brief

        self._target_type = target_type

        if default is not MISSING:
            try:
                valid_default = isinstance(default, target_type)
            except TypeError:
                # Generic in second argument to isinstance()
                valid_default = isinstance(default, get_origin(target_type))

            if not valid_default:
                e = "default for {!r} must be of type {}, not {}"
                raise TypeError(e.format(name, target_type, type(default)))

        self._default = default
        self._n_args = Range(*sorted(n_args))

    @classmethod
    def from_parameter(
        cls,
        parameter: inspect.Parameter,
        /,
        brief: str,
        target_type: Type[Any],
    ) -> Self:
        kwargs: Dict[str, Any] = {
            "name": parameter.name,
            "brief": brief,
            "target_type": target_type,
            "default": (
                parameter.default
                if parameter.default is not inspect.Parameter.empty
                else MISSING
            ),
        }

        if hasattr(parameter, "__metadata__"):
            metadata = getattr(parameter, "__metadata__")
            kwarg_map = convert_metadata(metadata)
            kwargs.update(**kwarg_map)

        return cls(**kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def target_type(self) -> Type[Any]:
        return self._target_type

    @property
    def default(self) -> Any:
        return self._default

    @property
    def n_args(self) -> Range:
        return self._n_args

    @property
    def help_info(self) -> HelpInfo:
        brief = self.brief

        if self.default is not MISSING:
            if self.target_type not in (bool,):
                brief += " [{}]".format(self.default)
            else:
                pass
        else:
            brief += " (required)"

        return {"name": self.name, "brief": brief}


class Option(Positional):

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
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            brief=brief,
            target_type=target_type,
            default=default,
            n_args=n_args,
            **kwargs,
        )

        if len(alias) > 1:
            raise ValueError("option alias must be a single character or None")

        self._alias = Alias(alias)
        self._requires = Requires(*requires or set())
        self._conflicts = Conflicts(*conflicts or set())

    @property
    def alias(self) -> Alias:
        return self._alias

    @property
    def requires(self) -> Requires[str]:
        return self._requires

    @property
    def conflicts(self) -> Conflicts[str]:
        return self._conflicts

    @property
    def help_info(self) -> HelpInfo:
        name = "--{}".format(self.name)

        if self.alias:
            name = "-{}, ".format(self.alias) + name

        data = super().help_info
        data.update(name=name)
        return data


DEFAULT_HELP = Option(
    "help",
    "Shows this help message and exits",
    target_type=bool,
    default=False,
    n_args=(0, 0),
    alias="h",
)
