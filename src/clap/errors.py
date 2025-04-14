from __future__ import annotations

import types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .abc import SupportsOptions, SupportsSubcommands


class ClapException(Exception):
    """The base exception for all clap-related exceptions"""


class SubcommandAlreadyExistsError(ClapException):
    """There was a problem adding a command to the parser"""

    def __init__(
        self, parent: SupportsSubcommands, command_name: str, *args: object
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
            f"option {option_name!r} already exists for {parent_name!r}"
        )


class ArgumentError(ClapException):
    """Represents an error that will be shown to the end user"""


class MissingRequiredArgumentError(ClapException):
    """Missing value for a required argument."""


class InvalidSignatureError(ClapException):
    pass


class MissingSetupFunctionError(ClapException):
    def __init__(self, module: types.ModuleType, *args: object) -> None:
        name = module.__name__

        super().__init__(
            f"module {name!r} is missing the required function 'setup'"
        )


class UserError(ClapException):
    """Custom exception to be shown to the user via the command-line."""
