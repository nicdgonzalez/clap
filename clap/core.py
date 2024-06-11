from __future__ import annotations

import importlib

# import inspect
from typing import TYPE_CHECKING

from .abc import CallableArgument, HasCommands

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import tuple as Tuple
    from builtins import type as Type
    from typing import Any, Optional

# fmt: off
__all__ = (
    "Extension",
    "Application",
    "Script",
)
# fmt: on


class ExtensionMeta(type):

    def __new__(
        cls, name: str, bases: Tuple[Type, ...], attrs: Dict[str, Any]
    ) -> ExtensionMeta:
        attrs["_name"] = name
        commands_map = attrs["_commands"] = {}
        assert commands_map == commands_map  # ignore unused var lsp error
        return super().__new__(cls, name, bases, attrs)


class Extension(HasCommands, metaclass=ExtensionMeta):

    @property
    def all_commands(self) -> Dict[str, CallableArgument]:
        return self._commands


class ParserBase: ...


class Application(ParserBase, HasCommands):

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


class Script(ParserBase): ...
