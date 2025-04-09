from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    MutableMapping,
    MutableSequence,
    Protocol,
    Sequence,
    overload,
    runtime_checkable,
)

from .converter import convert
from .errors import CommandAlreadyExistsError, OptionAlreadyExistsError

if TYPE_CHECKING:
    from .argument import Argument
    from .command import Command
    from .help import HelpFormatter, Usage
    from .option import Option


@runtime_checkable
class HasName(Protocol):
    @property
    def name(self) -> str:
        raise NotImplementedError


@runtime_checkable
class HasBrief(Protocol):
    @property
    def brief(self) -> str:
        raise NotImplementedError


@runtime_checkable
class SupportsOptions(Protocol):
    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        raise NotImplementedError

    @property
    def options(self) -> Sequence[Option[Any]]:
        # Filter out aliases.
        return [v for k, v in self.all_options.items() if k == v.name]

    def add_option(self, option: Option[Any], /) -> None:
        try:
            self.all_options[option.name]
        except KeyError:
            self.all_options[option.name] = option
        else:
            raise OptionAlreadyExistsError(self, option.name)

        if option.short is None:
            return

        try:
            self.all_options[option.short]
        except KeyError:
            self.all_options[option.short] = option
        else:
            _ = self.all_options.pop(option.name)
            raise OptionAlreadyExistsError(self, option.short)

    def remove_option(self, name: str) -> Option[Any] | None:
        if (option := self.all_options.pop(name)) is None:
            return None

        if option.short is None:
            return option

        if name == str(option.short):
            option.short = None
        else:
            _ = self.all_options.pop(option.short)

        return option


@runtime_checkable
class SupportsCommands(Protocol):
    @property
    def all_commands(self) -> MutableMapping[str, Command[Any]]:
        raise NotImplementedError

    @property
    def commands(self) -> Sequence[Command[Any]]:
        # Filter out aliases.
        return [v for k, v in self.all_commands.items() if k == v.name]

    @property
    def invoke_without_command(self) -> bool:
        return False

    def add_command(self, command: Command[Any], /) -> None:
        previous_parent = command.parent
        command.parent = self

        try:
            assert isinstance(command, HasName)
            self.all_commands[command.name]
        except KeyError:
            self.all_commands[command.name] = command
        else:
            command.parent = previous_parent
            raise CommandAlreadyExistsError(self, command.name)

        # To be able to reverse and undo if we encounter an error.
        aliases = command.aliases[slice(0, None, 1)]

        for alias in aliases:
            try:
                # Check if the alias clashes with an existing command.
                self.all_commands[alias]
            except KeyError:
                self.all_commands[alias] = command
            else:
                # Cancel the operation; remove the command and all of
                # the aliases that have already been added.
                _ = self.remove_command(command.name)

                # -1 to exclude the current alias since we never added it.
                index = aliases.index(alias) - 1
                reversed_aliases = aliases[slice(index, None, -1)]

                for alias in reversed_aliases:
                    _ = self.remove_command(alias)

                command.parent = previous_parent
                raise CommandAlreadyExistsError(self, alias)

    def remove_command(self, name: str, /) -> Command[Any] | None:
        if (command := self.all_commands.pop(name)) is None:
            # There was no command registered with this name.
            return None

        if len(command.aliases) < 1:
            return command

        if name in command.aliases:
            command.aliases.remove(name)
        else:
            for alias in command.aliases:
                _ = self.all_commands.pop(alias, None)

        return command


@runtime_checkable
class SupportsArguments(Protocol):
    @property
    def arguments(self) -> MutableSequence[Argument[Any]]:
        raise NotImplementedError

    def add_argument(self, argument: Argument[Any], /) -> None:
        self.arguments.append(argument)

    @overload
    def remove_argument(self, name: str, /) -> None: ...

    @overload
    def remove_argument(self, index: int, /) -> None: ...

    def remove_argument(self, query: str | int, /) -> Argument[Any] | None:
        match query:
            case int():
                return self.arguments.pop(query)
            case str():
                for index, argument in enumerate(self.arguments):
                    if query != argument.name:
                        continue

                    return self.arguments.pop(index)
            case _:
                raise TypeError(f"expected str or int, not {type(query)}")

        return None


@runtime_checkable
class SupportsConvert[T](Protocol):
    @property
    def target_type(self) -> Callable[[str], T]:
        raise NotImplementedError

    @property
    def default_value(self) -> T:
        raise NotImplementedError

    def convert(self, value: str) -> T:
        return convert(
            argument=value,
            converter=self.target_type,
            default=self.default_value,
        )


@runtime_checkable
class SupportsHelpMessage(Protocol):
    @property
    def usage(self) -> Usage:
        raise NotImplementedError

    def generate_help_message(self, fmt: HelpFormatter) -> str:
        raise NotImplementedError
