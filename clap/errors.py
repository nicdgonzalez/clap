from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from .abc import HasCommands, HasOptions, HasPositionalArgs
    from .lexer import Token

__all__ = (
    "ClapException",
    "CommandRegistrationError",
    "OptionRegistrationError",
    "InvalidCommandError",
    "InvalidOptionError",
    "TooManyArgumentsError",
)


class ClapException(Exception):
    pass


class CommandRegistrationError(ClapException):
    message: ClassVar[str] = "{0} {1!r} already exists in parent {2!r}"

    def __init__(
        self,
        parent: HasCommands,
        name_or_alias: str,
        *args: Any,
        alias_conflict: bool = False,
    ) -> None:
        t = "Alias" if alias_conflict else "Command"
        m = self.message.format(t, name_or_alias, parent.name)
        super().__init__(m, *args)


class OptionRegistrationError(ClapException):
    message: ClassVar[str] = "{0} {1!r} already exists in parent {2!r}"

    def __init__(
        self,
        parent: HasOptions,
        name_or_alias: str,
        *args: Any,
        alias_conflict: bool = False,
    ) -> None:
        t = "Alias" if alias_conflict else "Option"
        m = self.message.format(t, name_or_alias, parent.name)
        super().__init__(m, *args)


class InvalidCommandError(ClapException):

    def __init__(self, obj: HasCommands, token: Token) -> None:
        m = "{} is not a valid command on {!r}"
        super().__init__(m.format(token.value, obj.name))


class InvalidOptionError(ClapException):

    def __init__(self, obj: HasOptions, token: Token) -> None:
        m = "{} is not a valid option on {!r}"
        super().__init__(m.format(token.value, obj.name))


class TooManyArgumentsError(ClapException):

    def __init__(self, obj: HasPositionalArgs, token: Token) -> None:
        m = "too many arguments provided to {}: {}"
        args = [*obj.all_positionals, token]
        super().__init__(m.format(obj.name, ",".join(args)))
