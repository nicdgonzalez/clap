from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, overload, runtime_checkable

from .errors import CommandRegistrationError, OptionRegistrationError

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import set as Set
    from typing import Any, Callable, Optional, Union

    from .arguments import Positional
    from .options import Option


@runtime_checkable
class Argument(Protocol):

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def brief(self) -> str:
        raise NotImplementedError


@runtime_checkable
class CallableArgument(Argument, Protocol):
    """An abstract base class that details common operations for command-line
    arguments that map to an invokable function.

    The following classes implement this ABC:

    * :class:`Application`
    * :class:`Command`
    * :class:`Group`
    """

    @property
    def callback(self) -> Callable[..., Any]:
        raise NotImplementedError

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def aliases(self) -> List[str]:
        raise NotImplementedError

    @property
    def parent(self) -> Optional[HasCommands]:
        raise NotImplementedError

    @parent.setter
    def parent(self, parent: HasCommands) -> None:
        raise NotImplementedError


@runtime_checkable
class ParameterizedArgument(Argument, Protocol):
    """An abstract base class that details common operations for command-line
    arguments that map to parameters defined by a :class:`CallableArgument`.

    The following classes implement this ABC:

    * :class:`Positional`
    * :class:`Option`
    """

    pass


@runtime_checkable
class HasCommands(CallableArgument, Protocol):

    @property
    def all_commands(self) -> Dict[str, CallableArgument]:
        raise NotImplementedError

    @property
    def commands(self) -> Set[CallableArgument]:
        # filter out aliases while retaining the original order
        return {v for k, v in self.all_commands.items() if k == v.name}

    def add_command(self, command: CallableArgument, /) -> None:
        if command.name in self.all_commands.keys():
            raise CommandRegistrationError(self, command.name)

        if isinstance(self, HasCommands):
            command.parent = self

        self.all_commands[command.name] = command
        # we need to maintain an ordered list of aliases to be able to reverse
        # and undo if we encounter an error during registration
        aliases = [a for a in command.aliases]

        for alias in aliases:
            if alias not in self.all_commands.keys():
                self.all_commands[alias] = command
            else:
                _ = self.remove_command(command.name)

                # -1 to exclude current alias when reversing the list
                index = aliases.index(alias) - 1
                reversed_aliases = aliases[index::-1]

                for previously_added_alias in reversed_aliases:
                    _ = self.remove_command(previously_added_alias)

                raise CommandRegistrationError(
                    self, alias, alias_conflict=True
                )

    def remove_command(self, name: str, /) -> Optional[CallableArgument]:
        if (command := self.all_commands.pop(name, None)) is None:
            return None

        if len(command.aliases) < 1:
            return None

        if name in command.aliases:
            command.aliases.remove(name)
        else:
            for alias in command.aliases:
                _ = self.all_commands.pop(alias, None)

        return command


@runtime_checkable
class HasOptions(CallableArgument, Protocol):

    @property
    def all_options(self) -> Dict[str, Option]:
        raise NotImplementedError

    @property
    def options(self) -> Set[Option]:
        # filter out aliases while retaining the original order
        return {v for k, v in self.all_options.items() if k == v.name}

    def add_option(self, option: Option, /) -> None:
        if option.name in self.all_options.keys():
            raise OptionRegistrationError(self, option.name)

        self.all_options[option.name] = option

        if option.alias is None:
            return

        if option.alias in self.all_options.keys():
            _ = self.all_options.pop(option.name)

            raise OptionRegistrationError(
                self, option.alias, alias_conflict=True
            )

        self.all_options[option.alias] = option

    def remove_option(self, name: str, /) -> Optional[Option]: ...


@runtime_checkable
class HasPositionalArgs(CallableArgument, Protocol):

    @property
    def all_positionals(self) -> List[Positional]:
        raise NotImplementedError

    def add_positional(self, positional: Positional, /) -> None:
        self.all_positionals.append(positional)

    @overload
    def remove_positional(self, name: str, /) -> Optional[Positional]: ...

    @overload
    def remove_positional(self, index: int, /) -> Optional[Positional]: ...

    def remove_positional(
        self, name_or_index: Union[str, int], /
    ) -> Optional[Positional]:
        if isinstance(name_or_index, int):
            return self.all_positionals.pop(name_or_index)
        elif isinstance(name_or_index, str):
            for index, positional in enumerate(self.all_positionals):
                if positional.name == name_or_index:
                    return self.all_positionals.pop(index)
            else:
                return None
        else:
            raise TypeError(
                "name_or_index expected type str | int, "
                "got {}".format(type(name_or_index))
            )
