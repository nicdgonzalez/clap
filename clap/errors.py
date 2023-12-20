"""
Errors
======

This module contains all of the custom exceptions used by CLAP.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from .commands import Command, SupportsCommands


class ClapException(Exception):
    """Base exception for CLAP-related errors."""

    pass


class CommandRegistrationError(ClapException):
    """An exception for when a command cannot be added to a parent object.

    Parameters
    ----------
    parent : :class:`SupportsCommands`
        The object that the command could not be added to.
    command : :class:`Command`
        The command that could not be added.
    alias_conflict : :class:`bool`
        Whether the command could not be added due to an alias conflict.
    """

    message: ClassVar[str] = "{0} {1!r} cannot be added to parent {2!r}."

    def __init__(
        self,
        parent: SupportsCommands,
        command: Command[Any],
        *args: Any,
        alias_conflict: bool = False,
    ) -> None:
        s = "Alias" if alias_conflict else "Command"
        m = self.message.format(s, command.name, parent.name), *args
        super().__init__(m, *args)
