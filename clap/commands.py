"""
Core
====

This module contains the core classes and functions of the package.

Examples
--------
>>> import clap
>>>
>>>
>>> class ExampleCLI(clap.Parser):
...     \"\"\"Represents a collection of commands for the Example CLI.\"\"\"
...
...     def __init__(self, *args, **kwargs):
...         super().__init__(
...             help="A command-line tool for managing servers.",
...             epilog="Thank you for using Example CLI!",
...             *args,
...             **kwargs,
...         )
...         # do normal object initialization stuff here
...         ...
...
...     @clap.group()
...     def add(self, *args: Any, **kwargs: Any) -> None:
...         \"\"\"A group of commands for adding things.\"\"\"
...         pass
...
...     @add.command()
...     def user(self, id: int, /, *, admin: bool = False) -> None:
...         \"\"\"Adds a user to the system.
...
...         Parameters
...         ----------
...         id : int
...             The ID of the user to add.
...         admin : bool, default=False
...             Whether the user should be an administrator.
...         \"\"\"
...         ...

"""
from __future__ import annotations

import inspect
import re
import sys
from typing import (
    Any,
    Callable,
    Generic,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    get_type_hints,
)

from .arguments import Argument, DefaultHelp, Option
from .help import HelpBuilder, HelpFormatter, HelpItem
from .metadata import Conflicts, Range, Requires, Short
from .utils import MISSING, fold_text

__all__ = (
    "HasCommands",
    "Command",
    "command",
    "Group",
    "group",
)

T = TypeVar("T")
P = ParamSpec("P")

COMMAND_HELP_REGEX = re.compile(r"^(.*?)(?:\n\n|\Z)", re.DOTALL)
COMMAND_LONG_DESCRIPTION_REGEX = re.compile(
    r"^(?:.*?\n\n)(.*?)(?:\n\n|\Z)", re.DOTALL
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


class Command(Generic[T]):
    """Represents an executable command on the command-line.

    Parameters
    ----------
    callback : Callable
        The function to wrap.

    Attributes
    ----------
    callback : Callable
        The function wrapped by the command.
    name : str
        The name of the command.
    help : str
        The help message for the command.
    arguments : list[Argument[Any]]
        The arguments of the command.
    options : dict[str, Option[Any]]
        The options of the command.
    short_option_map : dict[str, str]
        A mapping of short option names to their full names.
    """

    def __init__(self, callback: Callable[P, T], /, **kwargs: Any) -> None:
        self.parent: HasCommands | None = kwargs.get("parent", None)
        if not callable(callback):
            raise TypeError(
                f"Command callback must be callable, not {type(callback)!r}"
            )
        else:
            self.callback = callback

        self.name: str = kwargs.pop("name") or callback.__name__

        parsed_docstring = _parse_docstring(callback)
        self.help = kwargs.pop("help", parsed_docstring["help"])
        self.arguments: list[Argument[Any]] = kwargs.get("arguments", [])
        self.options: dict[str, Option[Any]] = kwargs.get("options", {})
        self.short_option_map: dict[str, str] = kwargs.get(
            "short_option_map", {}
        )
        self.add_option(DefaultHelp)

        parameters = inspect.signature(callback).parameters
        parsed_descriptions: dict[str, str] = parsed_docstring["parameters"]
        parameter_types = get_type_hints(callback, include_extras=True)
        for parameter in parameters.values():
            if parameter.name == "self":
                continue

            argument = self._create_argument(
                parameter, parsed_descriptions, parameter_types
            )

            if isinstance(argument, Option):
                self.options[argument.name] = argument
            else:
                self.arguments.append(argument)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.parent is not None:
            return self.callback(self.parent, *args, **kwargs)  # type: ignore
        else:
            return self.callback(*args, **kwargs)

    def print_help(self, *, help_fmt: HelpFormatter = HelpFormatter()) -> None:
        """Display the help message for the command.

        Parameters
        ----------
        help_fmt : HelpFormatter, optional
            The help formatter to use for formatting the help message.
        """
        builder = HelpBuilder(formatter=help_fmt)
        builder.add_line(self.help)

        usage = self.name
        if self.options:
            usage += " [OPTIONS]"

        optional_remaining = False
        for argument in self.arguments:
            if not optional_remaining and argument.default is not MISSING:
                optional_remaining = True
            fmt = " <%s>" if not optional_remaining else " [%s]"
            usage += fmt % argument.name.upper()

        builder.add_header("USAGE", usage)

        if self.options:
            builder.add_header("OPTIONS")
            for option in self.options.values():
                builder.add_item(option)

        if self.arguments:
            builder.add_header("ARGUMENTS")
            for argument in self.arguments:
                builder.add_item(argument)

        sys.stdout.write(builder.build())

    def help_item_format(self) -> HelpItem:
        """Implement the :protocol:`HasHelpItemFormat` protocol.

        Returns
        -------
        HelpItem
            The name and description of the command to use in the help message.
        """
        return HelpItem(self.name, self.help)

    def add_option(self, option: Option[Any]) -> None:
        """Add an option to the command.

        Parameters
        ----------
        option : Option[Any]
            The option to add.
        """
        if option.name in self.options:
            raise ValueError(f"Option {option.name!r} already exists.")
        self.options[option.name] = option

        if option.short is not MISSING:
            if option.short in self.short_option_map:
                raise ValueError(
                    f"Short option {option.short!r} already exists."
                )
            self.short_option_map[option.short] = option.name

    def remove_option(self, name: str) -> None:
        """Remove an option from the command.

        Parameters
        ----------
        name : str
            The name of the option to remove.
        """
        if name not in self.options:
            raise ValueError(f"Option {name!r} does not exist.")
        del self.options[name]

        for k, v in self.short_option_map.items():
            if v == name:
                del self.short_option_map[k]
                break

    def add_argument(self, argument: Argument[Any]) -> None:
        """Add an argument to the command.

        Parameters
        ----------
        argument : Argument[Any]
            The argument to add.
        """
        self.arguments.append(argument)

    def remove_argument(self, name: str) -> None:
        """Remove an argument from the command.

        Parameters
        ----------
        name : str
            The name of the argument to remove.
        """
        for i, argument in enumerate(self.arguments):
            if argument.name == name:
                del self.arguments[i]
                break
        else:
            raise ValueError(f"Argument {name!r} does not exist.")

    def _create_argument(
        self,
        parameter: inspect.Parameter,
        descriptions: dict[str, str],
        types: dict[str, type[Any]],
        **attrs: Any,
    ) -> Argument[Any] | Option[Any]:
        """Return a initialized command-line argument based on the given
        parameter in the function's signature.

        Parameters
        ----------
        parameter : inspect.Parameter
            The parameter to create the argument from.
        descriptions : dict[str, str]
            A dictionary mapping the names of the parameters to their
            descriptions.
        attrs : Any
            Additional keyword arguments to pass to the constructor.

        Returns
        -------
        Argument[Any]
            The initialized argument.
        """
        Empty = inspect.Parameter.empty
        data = {
            "name": (name := parameter.name),
            "default": (
                parameter.default
                if parameter.default is not Empty
                else MISSING
            ),
        }

        try:
            data["help"] = attrs.get("help", descriptions[name])
        except KeyError:
            raise ValueError(
                f"Missing documentation for parameter {name!r} of "
                f"function {self.callback.__name__!r}"
            )

        try:
            cls = attrs.get("cls", types[name])

            if cls is inspect.Parameter.empty:
                raise TypeError
        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Missing type annotation for parameter {name!r} of "
                f"function {self.callback.__name__!r}"
            ) from e

        if hasattr(cls, "__metadata__"):
            metadata = cls.__metadata__
            for v in metadata:
                if isinstance(v, Short):
                    data["short"] = v
                elif isinstance(v, Requires):
                    data["requires"] = v
                elif isinstance(v, Conflicts):
                    data["conflicts"] = v
                elif isinstance(v, Range):
                    data["range"] = (v.minimum, v.maximum)
                else:
                    continue  # TODO: Log a warning here.

        if hasattr(cls, "__origin__"):
            cls = cls.__origin__

        data["cls"] = cls

        data.update(attrs)
        return self._get_argument_type(parameter)(**data)

    def _get_argument_type(
        self, parameter: inspect.Parameter, /
    ) -> type[Argument[Any]] | type[Option[Any]]:
        """Factory method for getting the type to use when converting a
        parameter to a command-line object.

        Parameters
        ----------
        parameter : inspect.Parameter
            The parameter to get the type for.

        Returns
        -------
        Argument | Option
            The type to use for the parameter.
        """
        k: TypeAlias = inspect.Parameter
        if parameter.kind in {k.POSITIONAL_ONLY, k.VAR_POSITIONAL}:
            return Argument
        elif parameter.kind in {
            k.POSITIONAL_OR_KEYWORD,
            k.KEYWORD_ONLY,
            k.VAR_KEYWORD,
        }:
            return Option
        else:
            raise NotImplementedError


class Group:
    """Represents a group of related commands.

    Parameters
    ----------
    name : str
        The name of the command group.

    Attributes
    ----------
    name : str
        The name of the command group.
    commands : dict[str, Command]
        The commands in the group.
    """

    def __init__(
        self, callback: Callable[P, T], /, name: str, *args: Any, **kwargs: Any
    ) -> None:
        self.parent: HasCommands | None = kwargs.get("parent", None)
        if not callable(callback):
            raise TypeError(
                f"Command callback must be callable, not {type(callback)!r}"
            )
        else:
            self.callback = callback

        self.name = name or callback.__name__
        self.help = kwargs.pop("help", _parse_docstring(callback)["help"])
        self.commands: dict[str, Command[Any] | Group] = {}
        self.options: dict[str, Option[Any]] = kwargs.get("options", {})
        self.short_option_map: dict[str, str] = kwargs.get(
            "short_option_map", {}
        )
        self.add_option(DefaultHelp)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        if args or kwargs:
            raise TypeError("Command groups cannot be called with arguments.")
        else:
            self.print_help()

    def print_help(self, *, help_fmt: HelpFormatter = HelpFormatter()) -> None:
        """Display the help message for the group.

        Parameters
        ----------
        help_fmt : HelpFormatter, optional
            The help formatter to use for formatting the help message.
        """
        builder = HelpBuilder(formatter=help_fmt)
        builder.add_line(self.help)

        usage = self.name
        if self.options:
            usage += " [OPTIONS]"
        if self.commands:
            usage += " <COMMAND> [ARGUMENTS]"

        builder.add_header("USAGE", usage)

        if self.options:
            builder.add_header("OPTIONS")
            for option in self.options.values():
                builder.add_item(option)

        if self.commands:
            builder.add_header("COMMANDS")
            for command in self.commands.values():
                builder.add_item(command)

        sys.stdout.write(builder.build())

    def help_item_format(self) -> HelpItem:
        """Implement the :protocol:`HasHelpItemFormat` protocol.

        Returns
        -------
        HelpItem
            The name and description of the command group to use in the help
            message.
        """
        return HelpItem(self.name, self.help)

    def add_command(self, command: Command[Any] | Group) -> None:
        """Adds a command to the group.

        Parameters
        ----------
        command : Command[Any]
            The command to add.
        """
        if command.name in self.commands:
            raise ValueError(f"Command {command.name!r} already exists.")
        self.commands[command.name] = command

    def remove_command(self, name: str) -> None:
        """Removes a command from the group.

        Parameters
        ----------
        name : str
            The name of the command to remove.
        """
        if name not in self.commands:
            raise ValueError(f"Command {name!r} does not exist.")
        del self.commands[name]

    def add_option(self, option: Option[Any]) -> None:
        """Add an option to the command group.

        Parameters
        ----------
        option : Option[Any]
            The option to add.
        """
        if option.name in self.options:
            raise ValueError(f"Option {option.name!r} already exists.")
        self.options[option.name] = option

        if option.short is not MISSING:
            if option.short in self.short_option_map:
                raise ValueError(
                    f"Short option {option.short!r} already exists."
                )
            self.short_option_map[option.short] = option.name

    def remove_option(self, name: str) -> None:
        """Remove an option from the command group.

        Parameters
        ----------
        name : str
            The name of the option to remove.
        """
        if name == "help":
            raise ValueError("Cannot remove the help option.")

        if name not in self.options:
            raise ValueError(f"Option {name!r} does not exist.")
        del self.options[name]

        for k, v in self.short_option_map.items():
            if v == name:
                del self.short_option_map[k]
                break

    def command(
        self, name: str = MISSING, **attrs: Any
    ) -> Callable[[Callable[P, T]], Command[T]]:
        """A convenience wrapper for registering a command with the group.

        Parameters
        ----------
        name : str, optional
            The name of the command. If not provided, the name of the function
            will be used.
        cls : Type[T], optional
            The class to use for constructing the command. If not provided, the
            default `Command` class will be used.
        attrs : Any
            Additional keyword arguments to pass to the constructor.

        Returns
        -------
        Callable[[Callable[P, T]], T]
            The decorator.
        """

        def wrapper(func: Callable[P, T]) -> Command[T]:
            attrs.setdefault("parent", self.parent or self)
            c = command(name=name, **attrs)(func)
            self.add_command(c)
            return c

        return wrapper

    def group(
        self, name: str = MISSING, **attrs: Any
    ) -> Callable[[Callable[P, None]], Group]:
        """A convenience wrapper for registering a command group.

        Parameters
        ----------
        name : str, optional
            The name of the command group. If not provided, the name of the
            function will be used.
        cls : Type[T], optional
            The class to use for constructing the command group. If not
            provided, the default `Group` class will be used.
        attrs : Any
            Additional keyword arguments to pass to the constructor.

        Returns
        -------
        Callable[[Callable[P, T]], T]
            The decorator.
        """

        def wrapper(func: Callable[P, None]) -> Group:
            attrs.setdefault("parent", self)
            g = group(name=name, **attrs)(func)
            self.add_command(g)
            return g

        return wrapper


class HasCommands(Protocol):
    """Protocol for objects that provide commands."""

    commands: dict[str, Command[Any] | Group]

    def add_command(self, command: Command[Any] | Group, /) -> None:
        """Add a command to the object.

        Parameters
        ----------
        command : Command[Any]
            The command to add.
        """
        ...

    def remove_command(self, name: str, /) -> None:
        """Remove a command from the object.

        Parameters
        ----------
        name : str
            The name of the command to remove.
        """
        ...


def command(
    name: str = MISSING, **attrs: Any
) -> Callable[[Callable[P, T]], Command[T]]:
    """Decorator to register a function as a command.

    Parameters
    ----------
    name : str, optional
        The name of the command. If not provided, the name of the function will
        be used.
    attrs : Any
        Additional keyword arguments to pass to the constructor.

    Returns
    -------
    Callable[[Callable[P, T]], Command[T]]
        The decorator.
    """

    def decorator(callback: Callable[P, T], /) -> Command[T]:
        if isinstance(callback, Command):
            raise TypeError(f"Callback {callback!r} is already a command.")
        return Command(callback, name=name, **attrs)

    return decorator


def group(
    name: str = MISSING, **attrs: Any
) -> Callable[[Callable[P, None]], Group]:
    """Decorator to register a function as a command group.

    Parameters
    ----------
    name : str, optional
        The name of the command group. If not provided, the name of the
        function will be used.
    attrs : Any
        Additional keyword arguments to pass to the constructor.

    Returns
    -------
    Callable[[Callable[P, T]], Group]
        The decorator.
    """

    def decorator(callback: Callable[P, None], /) -> Group:
        if isinstance(callback, Group):
            raise TypeError(
                f"Callback {callback!r} is already a command group."
            )
        return Group(callback, name=name, **attrs)

    return decorator


def _parse_docstring(callback: Callable[..., Any], /) -> dict[str, Any]:
    """Extracts information from a function's docstring for auto-constructing
    commands.

    Parameters
    ----------
    callback : Callable
        The function to extract information from.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the extracted information.
    """
    if (docstring := inspect.getdoc(callback)) is None:
        raise ValueError(f"Function {callback.__name__!r} has no docstring")
    return {
        "help": _extract_command_help(docstring),
        "parameters": _extract_parameter_descriptions(docstring),
    }


def _extract_command_help(
    docstring: str,
    /,
    *,
    pattern: re.Pattern[str] = COMMAND_HELP_REGEX,
) -> str | None:
    """Extract the first line of a command's docstring as the help description.

    Parameters
    ----------
    docstring : str
        The docstring to extract the description from.
    pattern : re.Pattern[str], optional
        The pattern to use for extracting the description.

    Returns
    -------
    str
        The first line of the docstring of the function.
    None
        If the function has no docstring.
    """
    if (match := pattern.match(docstring)) is None:
        return None
    return fold_text(match.group(1))


def _extract_parameter_descriptions(
    docstring: str,
    /,
    *,
    section_pattern: re.Pattern[str] = PARAMETER_SECTION_REGEX,
    description_pattern: re.Pattern[str] = PARAMETER_DESCRIPTION_REGEX,
) -> dict[str, str]:
    """Extract the descriptions of the parameters of a function from its
    docstring.

    Parameters
    ----------
    docstring : str
        The docstring to extract the descriptions from.
    pattern : re.Pattern[str], optional
        The pattern to use for extracting the descriptions.

    Returns
    -------
    dict[str, str]
        A dictionary mapping the names of the parameters to their descriptions.
    """
    if (match := section_pattern.search(docstring)) is None:
        return {}
    return {
        name: fold_text(description)
        for name, description in description_pattern.findall(match.group(1))
    }
