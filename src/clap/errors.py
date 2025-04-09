from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .abc import SupportsCommands, SupportsOptions


class ClapException(Exception):
    """The base exception for all clap-related exceptions"""


class CommandAlreadyExistsError(ClapException):
    """There was a problem adding a command to the parser"""

    def __init__(
        self, parent: SupportsCommands, command_name: str, *args: object
    ) -> None:
        parent_name = parent.__class__.__name__

        super().__init__(
            f"command {command_name!r} already exists for {parent_name!r}"
        )


class OptionAlreadyExistsError(ClapException):
    """There was a problem adding an option to the parser"""

    def __init__(
        self, parent: SupportsOptions, option_name: str, *args: object
    ) -> None:
        parent_name = parent.__class__.__name__

        super().__init__(
            f"command {option_name!r} already exists for {parent_name!r}"
        )


class ArgumentError(ClapException):
    """Represents an error that will be shown to the end user"""


class CommandError(ClapException):
    pass


class InvalidCallbackError(CommandError):
    def __init__(self, *args: object) -> None:
        super().__init__("expected callback to be callable")
