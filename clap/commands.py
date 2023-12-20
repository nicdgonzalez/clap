"""
Commands
========

This module implements the :class:`Command` class, which represents a
command-line argument that triggers a callback function.

"""
from __future__ import annotations

import inspect
import logging
import re
import sys
from typing import (
    TYPE_CHECKING,
    Generic,
    Protocol,
    TypeVar,
    get_type_hints,
    runtime_checkable,
)

from .arguments import Argument, SupportsArguments, add_argument
from .errors import CommandRegistrationError
from .help import Help, HelpFormatter, HelpInfo
from .metadata import extract_metadata
from .options import DefaultHelp, Option, SupportsOptions, add_option
from .utils import MISSING, fold_text

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import set as Set
    from builtins import type as Type
    from typing import Any, Callable, Optional, Union

    from .groups import Group

__all__ = [
    "SupportsCommands",
    "Command",
    "command",
    "add_command",
    "remove_command",
]

T = TypeVar("T")

_log = logging.getLogger(__name__)


@runtime_checkable
class SupportsCommands(Protocol):
    """A protocol for objects that can have commands attached to them.

    Attributes
    ----------
    all_commands : :class:`dict`
        A mapping of command names to :class:`Command` instances.
    """

    all_commands: Dict[str, Union[Command[Any], Group]]


class Command(Generic[T]):
    """Represents a command-line argument that triggers a callback function.

    Attributes
    ----------
    callback : Callable[..., T]
        The function to call when the command is invoked.
    name : :class:`str`
        The name of the command.
    brief : :class:`str`
        A short description of the command.
    description : Optional[:class:`str`]
        Additional information about the command.
    aliases : :class:`list`
        A list of alternative names that can be used to invoke the command.
    options : :class:`dict`
        A mapping of option names to :class:`Option` instances.
    arguments : :class:`list`
        A list of :class:`Argument` instances.
    parent : :class:`SupportsCommands`
        The object that the command is attached to.
    """

    def __init__(
        self,
        callback: Callable[..., T],
        /,
        *args: Any,
        name: str = MISSING,
        brief: str = MISSING,
        description: Optional[str] = MISSING,
        aliases: List[str] = MISSING,
        all_options: Dict[str, Option[Any]] = MISSING,
        arguments: List[Argument[Any]] = MISSING,
        parent: Optional[SupportsCommands] = None,
        **kwargs: Any,
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable.")

        self.callback = callback
        self.name = name or callback.__name__

        parsed_doc = parse_docstring(inspect.getdoc(callback) or "")

        self.brief = brief or parsed_doc.get("__brief__", "")
        self.description = description or parsed_doc.get("__description__", "")

        self.aliases = aliases or []
        self.all_options = all_options or {}
        self.arguments = arguments or []

        if parent is not None and not isinstance(parent, SupportsCommands):
            raise TypeError(
                "parent must be an instance of type SupportsCommands."
            )

        self.parent = parent

        add_option(self, DefaultHelp)
        convert_command_parameters(self, parsed_doc)

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        return self.invoke(*args, **kwargs)

    @property
    def options(self) -> Set[Option[Any]]:
        """A set of all options that are attached to this command."""
        return set(self.all_options.values())

    @property
    def help_info(self) -> HelpInfo:
        return {"name": self.name, "brief": self.brief}

    def display_help(self, *, fmt: HelpFormatter) -> None:
        """Display this help message and exit.

        Parameters
        ----------
        fmt : :class:`HelpFormatter`
            The formatter to use when displaying the help message.
        """
        h = Help()
        h.add_line(self.brief)
        h.add_newline()

        if self.description:
            node = h.add_section("DESCRIPTION")
            node.add_item(brief=self.description)

        usage = self.name

        assert self.options, "Command must have at least the default help."
        options = " | ".join(
            f"--{option.name}" for option in set(self.all_options.values())
        )
        usage += f" [{options}]"

        for argument in self.arguments:
            fmt = " <%s>" if argument.default is MISSING else " [%s]"
            usage += fmt % argument.name

        h.add_section("USAGE", brief=usage)

        node = h.add_section("ALIASES", skip_if_empty=True)
        node.add_item(brief=", ".join(self.aliases)) if self.aliases else None

        node = h.add_section("OPTIONS", skip_if_empty=True)

        # Retain the order of the options for the help message.
        options = [v for k, v in self.all_options.items() if k == v.name]
        for option in options:
            node.add_item(**option.help_info)

        node = h.add_section("ARGUMENTS", skip_if_empty=True)

        for argument in self.arguments:
            node.add_item(**argument.help_info)

        message = h.build()
        sys.stdout.write(message)

    def invoke(self, *args: Any, **kwargs: Any) -> T:
        """Execute the underlying callback.

        Parameters
        ----------
        *args : :class:`Any`
            Positional arguments to pass to the callback.
        **kwargs : :class:`Any`
            Keyword arguments to pass to the callback.

        Returns
        -------
        T
            The return value of the underlying callback.
        """
        value: T

        if hasattr(self.callback, "__self__"):
            s = self.callback.__self__
            value = self.callback(s, *args, **kwargs)
        else:
            value = self.callback(*args, **kwargs)

        return value


def command(*args: Any, **attrs: Any) -> Callable[..., Command[Any]]:
    """A decorator that converts a function into a :class:`Command`.

    Parameters
    ----------
    *args : :class:`Any`
        Positional arguments to pass to the :class:`Command` constructor.
    **kwargs : :class:`Any`
        Keyword arguments to pass to the :class:`Command` constructor.

    Returns
    -------
    Callable[..., :class:`Command`]
        The decorated function.
    """

    def decorator(callback: Callable[..., T]) -> Command[T]:
        if isinstance(callback, Command):
            raise TypeError("callback is already a Command.")

        return Command(callback, *args, **attrs)

    return decorator


def add_command(
    parent: SupportsCommands, command: Union[Command[Any], SupportsCommands]
) -> None:
    """Insert a command into the parent object's command map.

    Parameters
    ----------
    parent : :class:`SupportsCommands`
        The object to add the command to.
    command : :class:`Command`
        The command to add.
    """
    if not isinstance(command, (Command, SupportsCommands)):
        raise TypeError(
            "command must be an instance of type Command, not "
            f"{type(command).__name__!r}."
        )

    if isinstance(parent, SupportsCommands):
        command.parent = parent

    if command.name not in parent.all_commands:
        parent.all_commands[command.name] = command
    else:
        raise CommandRegistrationError(parent, command)

    for alias in command.aliases:
        if alias in parent.all_commands:
            _ = remove_command(parent, command.name)

            # Remove the recently added aliases to ensure proper cleanup.
            # Failure to do so may result in the command map being left in
            # an inconsistent state if the subsequent exception is caught.
            for alias in command.aliases:
                _ = remove_command(parent, alias)

            raise CommandRegistrationError(
                parent, command, alias_conflict=True
            )

        # Mutable objects are passed by reference, so we can just
        # add the alias and it will function as expected.
        parent.all_commands[alias] = command


def remove_command(
    parent: SupportsCommands, name: str
) -> Optional[Command[Any]]:
    """Delete a command from the parent object's command map.

    Parameters
    ----------
    parent : :class:`SupportsCommands`
        The object to remove the command from.
    name : :class:`str`
        The name of the command to remove.

    Returns
    -------
    :class:`Command`
        The command that was removed.
    """
    command = parent.all_commands.pop(name, None)

    if command is None:
        return None

    if name in command.aliases:
        try:
            command.aliases.remove(name)
        except ValueError:
            pass

        return command

    for alias in command.aliases:
        _ = parent.all_commands.pop(alias, None)

    return command


COMMAND_HELP_REGEX = re.compile(r"^(.*?)(?:\n\n|\Z)", re.DOTALL)
COMMAND_DESCRIPTION_REGEX = re.compile(
    r"^(?:.*?\n\n)?(.*?)(?:Parameters\n---+.*?)?(?:\n\n|\Z)", re.DOTALL
)
SECTION_REGEX_FMT = r"{section_name}\n-+\n\s*(.*?)(?:\n\n|\Z)"
PARAMETER_SECTION_REGEX = re.compile(
    SECTION_REGEX_FMT.format(section_name="Parameters"), re.DOTALL
)
OTHER_PARAMETER_SECTION_REGEX = re.compile(
    SECTION_REGEX_FMT.format(section_name="Other Parameters"), re.DOTALL
)
PARAMETER_DESCRIPTION_REGEX = re.compile(
    r"(?P<name>\S+)\s*:.*?\n(?P<description>.*?)(?=\S+\s*:|\Z)", re.DOTALL
)


def parse_docstring(docstring: str) -> Dict[str, str]:
    """Extract command information from the function's docstring.

    Notes
    -----
    The dictionary keys and values are as follows:

    ``__brief__``:
        The command's brief. This is taken from the first line.
    ``__description__``:
        The command's description. This is taken from the the second paragraph
        of the docstring. If not found, this will be an empty string.

    Each function parameter should be documented under the
    ``Parameters`` and ``Other Parameters`` sections like so::

        Parameters
        ----------
        {name} : {type}
            {brief}

        Other Parameters
        ----------------
        {name} : {type}
            {brief}

    Each parameter will be added to the dictionary as follows:

    - ``{name}``: ``{brief}``

    Parameters
    ----------
    docstring : :class:`str`
        The docstring to parse.

    Returns
    -------
    :class:`dict`
        A dictionary containing the command's brief, description, and
        the briefs of all related options and arguments.
    """
    data: Dict[str, str] = {}

    data["__brief__"] = _extract_command_brief(docstring)
    data["__description__"] = _extract_command_description(docstring)

    data.update(_extract_parameter_descriptions(docstring))

    return data


def _extract_command_brief(
    docstring: str, /, *, pattern: re.Pattern[str] = COMMAND_HELP_REGEX
) -> str:
    if (match := pattern.search(docstring)) is None:
        return ""
    return fold_text(match.group(1))


def _extract_command_description(
    docstring: str, /, *, pattern: re.Pattern[str] = COMMAND_DESCRIPTION_REGEX
) -> str:
    if (match := pattern.search(docstring)) is None:
        return ""
    return fold_text(match.group(1))


def _extract_parameter_descriptions(
    docstring: str,
    /,
    *,
    patterns: Dict[re.Pattern[str], re.Pattern[str]] = {
        PARAMETER_SECTION_REGEX: PARAMETER_DESCRIPTION_REGEX,
        OTHER_PARAMETER_SECTION_REGEX: PARAMETER_DESCRIPTION_REGEX,
    },
) -> Dict[str, str]:
    data: Dict[str, str] = {}

    for section_pattern, description_pattern in patterns.items():
        match = section_pattern.search(docstring)

        if match is None:
            continue

        for name, description in description_pattern.findall(match.group(1)):
            data[name] = fold_text(description)

    return data


def convert_parameter(
    parameter: inspect.Parameter,
    /,
    *,
    descriptions: Dict[str, str],
    types: Dict[str, Type[Any]],
) -> Union[Argument[Any], Option[Any]]:
    """Transform a function parameter into an Argument or Option based on
    its type annotation.

    Parameters
    ----------
    parameter : :class:`inspect.Parameter`
        The parameter to convert.
    descriptions : :class:`dict`
        A mapping of parameter names to their descriptions as extracted
        from the function's docstring.
    types : :class:`dict`
        A mapping of parameter names to their type annotations.

    Returns
    -------
    :class:`Argument` or :class:`Option`
        The converted parameter.
    """
    data: Dict[str, Any] = {
        "name": (name := parameter.name),
        "default": (
            parameter.default
            if parameter.default is not inspect.Parameter.empty
            else MISSING
        ),
    }

    try:
        data["brief"] = descriptions[name]
    except KeyError as exc:
        raise ValueError(
            f"Missing description for parameter {name!r}."
        ) from exc

    try:
        data["target_type"] = types[name]
    except KeyError as exc:
        raise ValueError(
            f"Missing type annotation for parameter {name!r}."
        ) from exc

    kind_mapping = {
        inspect.Parameter.POSITIONAL_ONLY: Argument,
        inspect.Parameter.VAR_POSITIONAL: Argument,
        inspect.Parameter.POSITIONAL_OR_KEYWORD: Option,
        inspect.Parameter.KEYWORD_ONLY: Option,
        inspect.Parameter.VAR_KEYWORD: Option,
    }

    try:
        argument_type = kind_mapping[parameter.kind]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported parameter kind {parameter.kind!r}."
        ) from exc

    if hasattr(parameter, "__metadata__"):
        data.update(extract_metadata(parameter.__metadata__))

    return argument_type(**data)


class _CommandBase(SupportsArguments, SupportsOptions):
    """A protocol which acts as an unofficial base class for :class:`Command`
    and :class:`Group`. This is used to avoid circular imports/pretend that
    commands doesn't know :class:`Group` exists. (It's a hack, I know. I am
    desperately trying to avoid inheritance here.)

    Attributes
    ----------
    callback : Callable[..., T]
        The function to call when the command is invoked.
    arguments : :class:`list`
        A list of :class:`Argument` instances.
    options : :class:`dict`
        A mapping of option names to :class:`Option` instances.
    """

    callback: Callable[..., T]


def convert_command_parameters(
    obj: _CommandBase, descriptions: Dict[str, str]
) -> None:
    """Transform the callback's parameters into options and arguments.

    Parameters
    ----------
    obj : :class:`_CommandLike`
        The object whose :attr:`callback` attribute's parameters will be
        converted into options and arguments.
    descriptions : :class:`dict`
        A mapping of parameter names to their descriptions as extracted
        from the function's docstring.
    """
    signature = inspect.signature(obj.callback)
    parameters = signature.parameters
    parameter_values = [_ for _ in parameters.values()]

    if hasattr(obj.callback, "__self__"):
        # __self__ is the first parameter of a bound method.
        _ = parameter_values.pop(0)
    elif (
        inspect.isfunction(obj.callback)
        and "." in obj.callback.__qualname__
        and parameters.get("self") is not None
    ):
        # The callback is likely an unbound method (though we can't be sure).
        _ = parameter_values.pop(0)

    parameter_types = get_type_hints(obj.callback)

    for parameter in parameter_values:
        argument = convert_parameter(
            parameter,
            descriptions=descriptions,
            types=parameter_types,
        )

        if isinstance(argument, Option):
            add_option(obj, argument)
        elif isinstance(argument, Argument):
            add_argument(obj, argument)
        else:
            raise NotImplementedError
