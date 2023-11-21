"""
Argument
========

Represents an argument to a command.

"""
from __future__ import annotations

import functools
from typing import Any, Generic, TypeVar

from .help import HelpItem
from .metadata import Range
from .utils import MISSING

__all__ = (
    "Argument",
    "Option",
    "Switch",
)

T = TypeVar("T")


class Argument(Generic[T]):
    """Represents an argument to a command.

    Parameters
    ----------
    name : str
        The name of the argument.
    help : str
        The help message for the argument.
    cls : type[T]
        The type of the argument.
    default : T | None
        The default value of the argument.
    range : tuple[int | None, int | None]
        The range of values that can be passed to the argument. If the first
        or second element is None, then there is no lower or upper bound,
        respectively.
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        self.name = name
        self.help: str = kwargs.pop("help", MISSING)
        if not self.help:
            raise ValueError(f"Missing help for argument {name!r}.")
        self.cls: type[T] = kwargs.pop("cls", str)
        self.default: T = kwargs.pop("default", MISSING)
        self.range: Range = kwargs.pop("range", Range(0, 1))

    def __call__(self, value: Any, *args: Any, **kwargs: Any) -> T:
        if value is MISSING:
            if self.default is MISSING:
                raise ValueError(f"Missing value for argument {self.name!r}.")
            else:
                return self.default
        else:
            return self.cls(value)  # type: ignore

    def help_item_format(self) -> HelpItem:
        description = self.help
        if self.default is not MISSING:
            description += f" [default: {self.default!r}]"
        else:
            description += " (required)"
        return HelpItem(self.name, description)


class Option(Argument[T]):
    """Represents an option to a command.

    Parameters
    ----------
    name : str
        The name of the option.
    help : str
        The help message for the option.
    cls : type[T]
        The type of the option.
    default : Optional[T]
        The default value of the option.
    short : str, optional
        A single character alias for the option.
    requires : set[str]
        The names of the options that this option requires.
    conflicts : set[str]
        The names of the options that this option conflicts with.
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        name = name.replace("_", "-")
        super().__init__(name, **kwargs)
        self.short: str = kwargs.pop("short", MISSING)
        self.requires: set[str] = kwargs.pop("requires", set())
        self.conflicts: set[str] = kwargs.pop("conflicts", set())

    def help_item_format(self) -> HelpItem:
        name = ""
        if self.short is not MISSING:
            name += f"-{self.short}, "
        name += f"--{self.name}"

        description = self.help
        if self.default is not MISSING:
            description += f" [default: {self.default!r}]"
        elif self.cls is bool:
            description += " [default: False]"
        else:
            description += " (required)"

        return HelpItem(name, description)


Switch = functools.partial(Option, cls=bool, default=False, range=(0, 1))
DefaultHelp = Switch(
    name="help",
    help="Display this help message and exit.",
    short="h",
)
