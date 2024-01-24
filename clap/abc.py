from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

from .errors import CommandRegistrationError, OptionRegistrationError

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import type as Type
    from typing import Callable, Optional, Self, Union

    from .metadata import Range
    from .option import Option

__all__ = (
    "PositionalArgument",
    "CallableArgument",
    "SupportsCommands",
    "SupportsOptions",
    "SupportsPositionals",
)

T_co = TypeVar("T_co", covariant=True)


class Argument(Protocol):
    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def brief(self) -> str:
        raise NotImplementedError


@runtime_checkable
class PositionalArgument(Argument, Protocol[T_co]):
    """An abstract base class that details common operations for command-line
    arguments that belong to another argument.

    The following classes implement this ABC:

    * :class:`Positional`
    * :class:`Option`
    """

    @classmethod
    def from_parameter(cls, parameter: inspect.Parameter) -> Self:
        raise NotImplementedError

    @property
    def target_type(self) -> Type[T_co]:
        raise NotImplementedError

    @property
    def default_value(self) -> T_co:
        raise NotImplementedError

    @property
    def n_args(self) -> Range:
        raise NotImplementedError


@runtime_checkable
class CallableArgument(Argument, Protocol[T_co]):
    """An abstract base class that details common operations for command-line
    arguments that perform an action.

    The following classes implement this ABC:

    * :class:`ArgumentParser`
    * :class:`Command`
    * :class:`Group`

    Attributes
    ----------
    parent: Optional[:class:`SupportsCommands`]
        The object to whom this argument belongs to.
    """

    parent: Optional[SupportsCommands]

    @property
    def qualified_name(self) -> str:
        if self.parent is None:
            return self.name

        return f"{self.parent.qualified_name} {self.name}"

    @property
    def description(self) -> Optional[str]:
        raise NotImplementedError

    @property
    def aliases(self) -> Union[List[str], None]:
        raise NotImplementedError

    @property
    def callback(self) -> Optional[Callable[..., T_co]]:
        raise NotImplementedError

    def __call__(self, *args: Any, **kwargs: Any) -> T_co:
        if self.callback is None:
            raise AttributeError(
                f"{self.__class__.__name__} {self.name}'s callback is None"
            )

        value: T_co

        if hasattr(self.callback, "__self__"):
            s = self.callback.__self__
            value = self.callback(s, *args, **kwargs)
        else:
            value = self.callback(*args, **kwargs)

        return value


@runtime_checkable
class SupportsCommands(CallableArgument[Any], Protocol):
    all_commands: Dict[str, CallableArgument[Any]]

    @property
    def commands(self) -> List[CallableArgument[Any]]:
        # Exclude aliases while retaining the original order.
        return [v for k, v in self.all_commands.items() if k == v.name]

    def add_command(self, command: CallableArgument[Any], /) -> None:
        if command.name in self.all_commands.keys():
            raise CommandRegistrationError(self, command.name)

        if isinstance(self, SupportsCommands):
            command.parent = self

        self.all_commands[command.name] = command

        if not command.aliases:
            return  # Either aliases are not supported, or alias list is empty.

        for alias in command.aliases:
            if alias not in self.all_commands.keys():
                self.all_commands[alias] = command
            else:
                _ = self.remove_command(command.name)

                index = command.aliases.index(alias) - 1
                reversed_aliases = command.aliases[index::-1]

                for previously_added_alias in reversed_aliases:
                    _ = self.remove_command(previously_added_alias)

                raise CommandRegistrationError(
                    self, alias, alias_conflict=True
                )

    def remove_command(self, name: str) -> Optional[CallableArgument[Any]]:
        if (command := self.all_commands.pop(name, None)) is None:
            return None

        if command.aliases is None:
            return None  # Command does not support aliases

        if name in command.aliases:
            command.aliases.remove(name)
            return command

        for alias in command.aliases:
            _ = self.all_commands.pop(alias, None)

        return command


@runtime_checkable
class SupportsOptions(CallableArgument[Any], Protocol):
    all_options: Dict[str, Option[Any]]

    @property
    def options(self) -> List[Option[Any]]:
        # Exclude aliases while retaining the original order.
        return [v for k, v in self.all_options.items() if k == v.name]

    def add_option(self, option: Option[Any], /) -> None:
        if option.name in self.all_options.keys():
            raise OptionRegistrationError(self, option.name)

        self.all_options[option.name] = option

        if option.alias is None:
            return  # Alias is not set.

        if option.alias in self.all_options.keys():
            _ = self.all_options.pop(option.name)
            raise OptionRegistrationError(
                self, option.alias, alias_conflict=True
            )

        self.all_options[option.alias] = option

    def remove_option(self, name: str, /) -> Optional[Option[Any]]:
        if (option := self.all_options.pop(name, None)) is None:
            return None  # Nothing to remove; name is not a valid key.

        if option.alias is not None:
            if name == option.alias:
                option.alias = None
            else:
                _ = self.all_options.pop(option.alias, None)

        return option


@runtime_checkable
class SupportsPositionals(CallableArgument[Any], Protocol):
    ...
