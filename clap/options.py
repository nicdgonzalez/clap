from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

from .converter import convert
from .help import HelpInfo
from .metadata import Conflicts, Range, Requires, Short, extract_metadata
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import tuple as Tuple
    from builtins import type as Type
    from typing import Any, Iterable, Optional, Union

__all__ = [
    "Option",
    "SupportsOptions",
    "add_option",
    "remove_option",
    "DefaultHelp",
]

T = TypeVar("T")

_log = logging.getLogger(__name__)


class SupportsOptions(Protocol):
    """A protocol for objects that can have options attached to them.

    Attributes
    ----------
    options : :class:`list`
        A mapping of option names to :class:`Option` instances.
    """

    options: Dict[str, Option[Any]]


class Option(Generic[T]):
    """Represents a keyword-only argument to a :class:`Command`

    Attributes
    ----------
    name : :class:`str`
        The name of the option. This is used to identify the option.
    brief : :class:`str`
        A short description of the option. This is used in the help message.
    target_type : :class:`type`
        The type to which the option will be converted.
    default : :class:`T`
        The value to use for the option if no value is given.
    n_args : :class:`tuple`
        A tuple containing the minimum and maximum number of arguments that
        can be passed to the option.
    alias : :class:`str`
        A single-character alternative that can be used to identify the option.
        (e.g. ``-h`` for ``--help`` or ``-V`` for ``--version``)
    requires : :class:`Requires`
        A set of options that are required by this option.
    conflicts : :class:`Conflicts`
        A set of options that are mutually exclusive with this option.
    """

    def __init__(
        self,
        *args: Any,
        name: str,
        brief: str,
        target_type: Type[T] = MISSING,
        default: T = MISSING,
        n_args: Union[Range, Tuple[int, Optional[int]], int] = Range(0, 1),
        alias: Short = MISSING,
        requires: Requires = MISSING,
        conflicts: Conflicts = MISSING,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.brief = brief

        if target_type is MISSING:
            target_type = str

        self.target_type = target_type

        if default is not MISSING and not isinstance(default, target_type):
            _log.warning(
                f"Default value {default!r} is not an instance of "
                + f"{target_type!r}."
            )

        if default is MISSING and self.target_type is bool:
            default = False

        self.default = default

        if isinstance(n_args, int):
            n_args = Range(n_args, n_args)
        elif isinstance(n_args, tuple):
            n_args = Range(*n_args)
        elif not isinstance(n_args, Range):
            raise TypeError("n_args must be a tuple or Range")

        self.n_args = n_args

        if alias and len(alias) > 1:
            raise ValueError("alias must be a single character")

        self.alias = alias

        self.requires = requires or Requires()
        self.conflicts = conflicts or Conflicts()

    @classmethod
    def from_parameter(
        cls,
        parameter: inspect.Parameter,
        /,
        *,
        brief: str,
        target_type: Type[Any],
    ) -> Option[Any]:
        """Initialize an option from a :class:`inspect.Parameter` instance.

        Parameters
        ----------
        parameter : :class:`inspect.Parameter`
            The parameter to transform into an option.

        Returns
        -------
        :class:`Option`
            The option.
        """
        valid_kinds = {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD,
        }

        if parameter.kind not in valid_kinds:
            raise ValueError(
                f"Invalid parameter kind {parameter.kind!r} for option "
                + repr(parameter.name)
            )

        data = {
            "name": parameter.name,
            "brief": brief,
            "target_type": target_type,
            "default": (
                parameter.default
                if parameter.default is not inspect.Parameter.empty
                else MISSING
            ),
        }

        if hasattr(target_type, "__metadata__"):
            data.update(extract_metadata(target_type))

        return cls(**data)

    @property
    def as_snake_case(self) -> str:
        """Return the option as a snake_case string."""
        return self.name.replace("-", "_")

    @property
    def as_kebab_case(self) -> str:
        """Return the option as a kebab-case string."""
        return self.name.replace("_", "-")

    @property
    def takes_value(self) -> bool:
        """Return whether the option takes a value."""
        return self.n_args.maximum > 0

    @property
    def help_info(self) -> HelpInfo:
        """Get the help information for the argument.

        Returns
        -------
        :class:`dict`
            A dictionary containing the help information for the argument.
        """
        name = ""

        if self.alias is not MISSING:
            name += f"-{self.alias}, "

        name += f"--{self.name}"
        brief = self.brief

        if self.default is not MISSING:
            if self.target_type not in (bool,):
                brief += f" [default: {self.default}]"
        else:
            brief += " (required)"

        return {"name": name, "brief": brief}

    def convert(self, value: str) -> T:
        """Convert the given value to the option's target type.

        Parameters
        ----------
        value : :class:`str`
            The value to convert.

        Returns
        -------
        :class:`T`
            The converted value.
        """
        result: T = convert(self.target_type, value)

        if result is None:
            raise ValueError(f"Missing required option {self.name!r}.")

        return result

    def validate_conflicts(self, options: Iterable[str], /) -> None:
        """Validate that the given options do not conflict with this option.

        Parameters
        ----------
        options : :class:`Iterable`
            The options passed to the command.

        Raises
        ------
        :class:`ValueError`
            If any of the given options conflict with this option.
        """
        for option in options:
            if option in self.conflicts:
                raise ValueError(
                    f"Option {self.name!r} conflicts with option {option!r}."
                )

    def validate_requires(self, options: Iterable[str], /) -> None:
        """Validate that the given options are required by this option.

        Parameters
        ----------
        options : :class:`Iterable`
            The options passed to the command.

        Raises
        ------
        :class:`ValueError`
            If any of the given options are not required by this option.
        """
        for option in self.requires:
            if option not in options:
                raise ValueError(
                    f"Option {self.name!r} requires option {option!r}."
                )


DefaultHelp = Option[bool](
    name="help",
    brief="Show this message and exit.",
    target_type=bool,
    default=False,
    n_args=(0, 0),
    alias="h",
)


def add_option(obj: SupportsOptions, option: Option[Any]) -> None:
    """Create an entry in the given object's options dictionary.

    Parameters
    ----------
    obj : :class:`SupportsOptions`
        The object to which the option will be added.
    option : :class:`Option`
        The option to add.
    """
    if option.name in obj.all_options:
        raise ValueError(f"Option {option.name!r} already exists.")

    obj.all_options[option.name] = option

    if option.alias is MISSING:
        return

    if option.alias in obj.all_options:
        existing = obj.all_options[option.alias]
        _ = remove_option(obj, option.name)
        raise ValueError(
            f"Option {existing.name!r} already uses alias {option.alias!r}."
        )

    obj.all_options[option.alias] = option


def remove_option(obj: SupportsOptions, /, name: str) -> Optional[Option[Any]]:
    """Remove an option from the given object, if it exists. This can also be
    used to remove an option's alias.

    Parameters
    ----------
    name : :class:`str`
        The name of the option to remove.
    obj : :class:`SupportsOptions`
        The object from which the option will be removed.

    Returns
    -------
    :class:`Option`
        The removed option.
    """
    option = obj.all_options.pop(name, None)

    if option is None:
        return None

    has_alias = option.alias is not MISSING

    if has_alias:
        if name == option.alias:
            option.alias = MISSING
        else:
            _ = obj.all_options.pop(option.alias, None)

    return option
