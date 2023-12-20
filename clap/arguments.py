"""
Arguments
=========

This module implements the :class:`.Argument` class, which represents an
argument to a :class:`.Command`.

"""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Protocol,
    TypeVar,
    overload,
    runtime_checkable,
)

from .converter import convert
from .help import HelpInfo
from .metadata import Range
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import type as Type
    from typing import Any, Optional, Union

__all__ = [
    "SupportsArguments",
    "Argument",
    "add_argument",
    "remove_argument",
]

T = TypeVar("T")


@runtime_checkable
class SupportsArguments(Protocol):
    """A protocol for objects that can have arguments attached to them.

    Attributes
    ----------
    arguments : :class:`list`
        A list of :class:`.Argument` instances.
    """

    arguments: List[Argument[Any]]


class Argument:
    """Represents an positional argument to a :class:`.Command`.

    Attributes
    ----------
    name : :class:`str`
        The name of the argument. This is used to identify the argument.
    brief : :class:`str`
        A short description of the argument. This is used in the help message.
    target_type : :class:`type`
        The type to which the argument will be converted.
    default : :class:`T`
        The value to use for the argument if no value is given.
    n_args : :class:`.Range`
        A tuple containing the minimum and maximum number of arguments that
        can be passed to the argument.
    """

    def __init__(
        self,
        name: str,
        brief: str,
        *args: Any,
        target_type: Type[T] = MISSING,
        default: T = MISSING,
        n_args: Range = Range(0, 1),
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.brief = brief

        if target_type is MISSING:
            target_type = str

        self.target_type = target_type

        if default is not MISSING and not isinstance(default, target_type):
            raise TypeError("default must be an instance of target_type")

        self.default = default

        if isinstance(n_args, tuple):
            n_args = Range(*n_args)
        elif not isinstance(n_args, Range):
            raise TypeError("n_args must be a tuple or Range")

        self.n_args = n_args

    @property
    def help_info(self) -> HelpInfo:
        """Get the help information for the argument.

        Returns
        -------
        :class:`dict`
            A dictionary containing the help information for the argument.
        """
        brief = self.brief

        if self.default is not MISSING:
            if self.target_type not in (bool,):
                brief += f" [default: {self.default}]"
        else:
            brief += " (required)"

        return {"name": self.name, "brief": brief}

    def convert(self, value: str) -> T:
        """Convert the given value to the argument's target type.

        Parameters
        ----------
        value : :class:`str`
            The value to convert.

        Returns
        -------
        :class:`T`
            The converted value as an instance of :attr:`target_type`.
        """
        result: T = convert(self.target_type, value)

        if result is None:
            raise ValueError(f"Missing value for argument {self.name!r}")

        return result


def add_argument(obj: SupportsArguments, argument: Argument[Any]) -> None:
    """Append an argument to the given object.

    Parameters
    ----------
    obj : :class:`.SupportsArguments`
        The object to which the argument will be added.
    argument : :class:`.Argument`
        The argument to add.
    """
    if not isinstance(argument, Argument):
        raise TypeError("argument must be an instance of type Argument")

    obj.arguments.append(argument)


@overload
def remove_argument(
    obj: SupportsArguments, /, name: str
) -> Optional[Argument[Any]]:
    ...


@overload
def remove_argument(
    obj: SupportsArguments, /, index: int
) -> Optional[Argument[Any]]:
    ...


def remove_argument(
    obj: SupportsArguments, /, name_or_index: Union[str, int]
) -> Optional[Argument[Any]]:
    """Remove an argument from the given object.

    Parameters
    ----------
    name_or_index : Union[:class:`str`, :class:`int`]
        The name or index of the argument to remove. If a name is given, the
        first argument with that name will be removed.
    obj : :class:`.SupportsArguments`
        The object from which the argument will be removed.
    """
    if not isinstance(name_or_index, (str, int)):
        raise TypeError("name_or_index must be an instance of type str or int")

    if isinstance(name_or_index, int):
        return obj.arguments.pop(name_or_index)

    for index, argument in enumerate(obj.arguments):
        if argument.name == name_or_index:
            return obj.arguments.pop(index)

    return None
