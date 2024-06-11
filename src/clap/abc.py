from typing import Protocol, runtime_checkable

from .argument import Argument
from .command import Command
from .option import Option


@runtime_checkable
class HasOptions(Protocol):
    @property
    def options(self) -> dict[str, Option]:
        raise NotImplementedError


@runtime_checkable
class HasCommands(HasOptions, Protocol):
    @property
    def commands(self) -> dict[str, Command]:
        raise NotImplementedError


@runtime_checkable
class HasArguments(HasOptions, Protocol):
    @property
    def arguments(self) -> list[Argument]:
        raise NotImplementedError
