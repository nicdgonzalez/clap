from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from .abc import HasCommands, HasOptions

__all__ = (
    "ClapException",
    "CommandRegistrationError",
    "OptionRegistrationError",
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
