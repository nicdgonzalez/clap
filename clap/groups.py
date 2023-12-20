"""
Groups
======

This module contains the :class:`Group` class, which is used to represent
a group of :class:`Command` objects.

"""
from __future__ import annotations

import inspect
import sys
from typing import TYPE_CHECKING

from .commands import (
    Command,
    SupportsCommands,
    add_command,
    convert_command_parameters,
    parse_docstring,
)
from .help import Help, HelpFormatter, HelpInfo
from .options import DefaultHelp, add_option
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import set as Set
    from typing import Any, Callable, Optional, Union

    from .option import Option

__all__ = [
    "Group",
    "group",
]

_NoneType = type(None)


class Group:
    """Represents a group of :class:`Command` objects.

    This class implements the :class:`SupportsCommands` protocol.

    .. note::

        This class is similar to :class:`Command`, except it does not accept
        positional arguments and instead takes subcommands. By default, the
        callback function is not called when the group is invoked without a
        subcommand (the help message is displayed instead). This behavior can
        be toggled using the :attr:`invoke_without_command` attribute.

    Attributes
    ----------
    callback : Callable[..., _NoneType]
        The function to call when the group is invoked.
    name : :class:`str`
        The name of the group.
    brief : :class:`str`
        A short description of the group.
    description : Optional[:class:`str`]
        Additional information about the group.
    aliases : :class:`list`
        A list of alternative names that can be used to invoke the group.
    options : :class:`dict`
        A mapping of option names to :class:`Option` instances.
    all_commands : :class:`dict`
        A mapping of command names to :class:`Command` and :class:`Group`
        instances.
    parent : Optional[:class:`SupportsCommands`]
        The parent of the group.
    invoke_without_command : :class:`bool`
        Whether the callback function should be called when the group is
        invoked without a subcommand, or if the help message should be
        displayed instead.
    """

    def __init__(
        self,
        callback: Callable[..., _NoneType],
        *args: Any,
        name: str = MISSING,
        brief: str = MISSING,
        description: Optional[str] = MISSING,
        aliases: List[str] = MISSING,
        all_options: Dict[str, Option[Any]] = MISSING,
        parent: Optional[SupportsCommands] = MISSING,
        invoke_without_command: bool = False,
        **kwargs: Any,
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be a callable object")

        self.callback = callback
        self.name = name or callback.__name__

        parsed_doc = parse_docstring(inspect.getdoc(callback) or "")

        self.brief = brief or parsed_doc.get("__brief__", "")
        self.description = description or parsed_doc.get("__description__", "")
        self.aliases = aliases or []
        self.all_options = all_options or {}
        add_option(self, DefaultHelp)

        if parent is not MISSING and not isinstance(parent, SupportsCommands):
            raise TypeError("parent must be an instance of SupportsCommands")

        self.parent = parent or None
        self.invoke_without_command = invoke_without_command

        self.all_commands: Dict[str, Union[Command[Any], SupportsCommands]]
        self.all_commands = {}
        accumulate_commands(self)
        convert_command_parameters(self, parsed_doc)

    @property
    def commands(self) -> Set[Command[Any]]:
        """A set of all the commands defined within this group.

        Returns
        -------
        :class:`set`
            A set of all the commands defined within this group.
        """
        return set(self.all_commands.values())

    @property
    def help_info(self) -> HelpInfo:
        return {"name": f"*{self.name}", "brief": self.brief}

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.invoke(*args, **kwargs)

    def display_help(self, *, fmt: HelpFormatter) -> None:
        """Display this help message and exit."""
        h = Help()
        h.add_line(self.brief)
        h.add_newline()

        if self.description:
            node = h.add_section("DESCRIPTION")
            node.add_item(brief=self.description)

        usage = self.name

        assert self.options, "Group must have at least the default help."
        options = " | ".join(
            f"--{option.name}" for option in self.all_options.values()
        )
        usage += f" [{options}]"

        h.add_section("USAGE", usage)

        node = h.add_section("ALIASES", skip_if_empty=True)
        node.add_item(brief=", ".join(self.aliases))

        node = h.add_section("OPTIONS", skip_if_empty=True)

        # Retain the order of the options for the help message.
        options = [v for k, v in self.all_options.items() if k == v.name]
        for option in options:
            node.add_item(**option.help_info)

        node = h.add_section(
            "COMMANDS",
            brief="'*' indicates a COMMAND GROUP",
            skip_if_empty=True,
        )

        # Retain the order of the commands for the help message.
        commands = [v for k, v in self.all_commands.items() if k == v.name]
        for command in commands:
            node.add_item(**command.help_info)

        message = h.build()
        sys.stdout.write(message)

    def invoke(self, *args: Any, **kwargs: Any) -> None:
        """Execute the underlying callback and display the help message.

        Parameters
        ----------
        *args: :class:`Any`
            Positional arguments to pass to the callback.
        **kwargs: :class:`Any`
            Keyword arguments to pass to the callback.
        """
        if self.invoke_without_command:
            if hasattr(self.callback, "__self__"):
                s = self.callback.__self__
                self.callback(s, *args, **kwargs)
            else:
                self.callback(*args, **kwargs)
        else:
            self.help.invoke()

    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[..., Command[Any]]:
        """A convenience wrapper for :func:`command` that automatically sets
        the :attr:`parent` attribute of the command to this group and adds the
        command to the :attr:`all_commands` dictionary.

        Parameters
        ----------
        *args: :class:`Any`
            Positional arguments to pass to the :class:`Command` constructor.
        **kwargs: :class:`Any`
            Keyword arguments to pass to the :class:`Command` constructor.

        Returns
        -------
        Callable[..., Command]
            A decorator that turns a function into a :class:`Command` object.
        """

        def decorator(callback: Callable[..., Any], /) -> Command[Any]:
            kwargs.setdefault("parent", self)
            c = Command(callback, *args, **kwargs)
            add_command(self, c)
            return c

        return decorator

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., Group]:
        """A convenience wrapper for :func:`group` that automatically sets
        the :attr:`parent` attribute of the group to this group and adds the
        group to the :attr:`all_commands` dictionary.

        Parameters
        ----------
        *args: :class:`Any`
            Positional arguments to pass to the :class:`Group` constructor.
        **kwargs: :class:`Any`
            Keyword arguments to pass to the :class:`Group` constructor.

        Returns
        -------
        Callable[..., Group]
            A decorator that turns a function into a :class:`Group` object.
        """

        def decorator(callback: Callable[..., _NoneType], /) -> Group:
            kwargs.setdefault("parent", self)
            g = Group(callback, *args, **kwargs)
            add_command(self, g)
            return g

        return decorator


def group(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[..., _NoneType]], Group]:
    """A decorator that turns a function into a :class:`Group` object.

    Parameters
    ----------
    *args: :class:`Any`
        Positional arguments to pass to the :class:`Group` constructor.
    **kwargs: :class:`Any`
        Keyword arguments to pass to the :class:`Group` constructor.

    Returns
    -------
    Callable[[Callable[..., _NoneType]], Group]
        A decorator that turns a function into a :class:`Group` object.
    """

    def decorator(callback: Callable[..., _NoneType], /) -> Group:
        if isinstance(callback, Group):
            raise TypeError("callback is already a Group object")

        return Group(callback, *args, **kwargs)

    return decorator


def accumulate_commands(obj: SupportsCommands) -> None:
    """Add all commands defined in the given object to the :attr:`all_commands`
    dictionary.

    Parameters
    ----------
    obj : :class:`SupportsCommands`
        The object that contains the commands.
    """

    def predicate(c: Any) -> bool:
        return isinstance(c, (Command, SupportsCommands))

    members = inspect.getmembers(obj, predicate=predicate)
    for _, cmd in members:
        if isinstance(obj, SupportsCommands):
            cmd.parent = obj

        # Decorators wrap around the unbound method, so we need to set the
        # __self__ attribute to the instance manually.
        if not hasattr(cmd.callback, "__self__"):
            cmd.callback.__self__ = obj

        add_command(obj, cmd)
