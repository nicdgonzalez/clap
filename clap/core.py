from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

from .abc import CallableArgument, HasCommands, HasOptions, HasPositionalArgs
from .commands import Command

if TYPE_CHECKING:
    from builtins import dict as Dict
    from typing import Any, Iterable, Optional, Union

    from typing_extensions import Self


# fmt: off
__all__ = (
    "Extension",
    "Application",
    "Script",
)
# fmt: on


class Extension(HasCommands):

    if TYPE_CHECKING:
        _name: str
        _commands: Dict[str, CallableArgument]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        this = super().__new__(cls)
        this._name = this.__class__.__name__
        this._commands = {}

        members = tuple(this.__class__.__dict__.values())
        for command in members:
            if not isinstance(command, CallableArgument):
                continue

            if isinstance(this, HasCommands):
                command.parent = this

            # Decorators on class methods wrap around the unbound method;
            # we need to set the `__self__` attribute manually
            if not hasattr(command.callback, "__self__"):
                setattr(command.callback, "__self__", this)

            this.add_command(command)

        return this

    @property
    def all_commands(self) -> Dict[str, CallableArgument]:
        return self._commands


class ParserBase:

    def parse_args(args: Iterable[str] = sys.argv, /) -> None: ...


class Application(ParserBase, HasCommands, HasOptions):

    def extend(self, name: str, package: Optional[str] = None) -> None:
        module = importlib.import_module(name, package=package)
        setup_fn = getattr(module, "setup", None)

        if setup_fn is None:
            raise AttributeError(
                "Module {!r} missing global 'setup' function".format(name)
            )

        _ = setup_fn(self)

    def add_extension(self, extension: Extension, /) -> None:
        for command in extension.commands:
            self.add_command(command)


class Script(ParserBase, HasOptions, HasPositionalArgs): ...
