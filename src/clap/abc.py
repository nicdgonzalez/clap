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
from .errors import OptionAlreadyExistsError, SubcommandAlreadyExistsError

if TYPE_CHECKING:
    from .group import Group
    from .help import HelpFormatter, Usage
    from .option import Option
    from .positional import PositionalArgument
    from .subcommand import Subcommand


@runtime_checkable
class Argument(Protocol):
    """A protocol that defines the common operations of a command-line
    argument.

    Most of the library's core functionality operates on this protocol
    in one way or another.

    Attributes
    ----------
    name
    brief
    """

    @property
    def name(self) -> str:
        """A name used to reference and identify this object."""
        raise NotImplementedError

    @property
    def snake_case(self) -> str:
        return self.name.replace("-", "_")

    @property
    def kebab_case(self) -> str:
        return self.name.replace("_", "-")

    @property
    def brief(self) -> str:
        """A short summary explaining the argument's purpose."""
        raise NotImplementedError


@runtime_checkable
class SupportsSubcommands(Protocol):
    """A protocol that defines the common operations for command-line
    arguments that perform specific tasks within a single command framework.

    Attributes
    ----------
    all_subcommands
    subcommands
    invoke_without_subcommand
    """

    @property
    def all_subcommands(
        self,
    ) -> MutableMapping[str, Group[Any] | Subcommand[Any]]:
        """A collection of subcommands for this argument."""
        raise NotImplementedError

    @property
    def subcommands(self) -> Sequence[Group[Any] | Subcommand[Any]]:
        """A collection of subcommands for this argument, excluding aliases."""
        return [v for k, v in self.all_subcommands.items() if k == v.name]

    @property
    def invoke_without_subcommand(self) -> bool:
        """Whether the argument can execute itself without a subcommand."""
        return False

    def add_subcommand(
        self,
        subcommand: Group[Any] | Subcommand[Any],
        /,
    ) -> None:
        """Register a new subcommand.

        Parameters
        ----------
        subcommand
            The subcommand to add.

        Raises
        ------
        SubcommandAlreadyExistsError
            A subcommand already exists with the same name (or alias).
        """
        previous_parent = subcommand.parent
        subcommand.parent = self

        try:
            assert isinstance(subcommand, Argument)
            self.all_subcommands[subcommand.name]
        except KeyError:
            self.all_subcommands[subcommand.name] = subcommand
        else:
            subcommand.parent = previous_parent
            raise SubcommandAlreadyExistsError(self, subcommand.name)

        # To be able to reverse and undo if we encounter an error.
        aliases = subcommand.aliases[slice(0, None, 1)]

        for alias in aliases:
            try:
                # Check if the alias clashes with an existing command.
                self.all_subcommands[alias]
            except KeyError:
                self.all_subcommands[alias] = subcommand
            else:
                # Cancel the operation; remove the command and all of
                # the aliases that have already been added.
                _ = self.remove_subcommand(subcommand.name)

                # -1 to exclude the current alias since we never added it.
                index = aliases.index(alias) - 1
                reversed_aliases = aliases[slice(index, None, -1)]

                for alias in reversed_aliases:
                    _ = self.remove_subcommand(alias)

                subcommand.parent = previous_parent
                raise SubcommandAlreadyExistsError(self, alias)

    def remove_subcommand(
        self, name: str, /
    ) -> Group[Any] | Subcommand[Any] | None:
        """Unregister a subcommand or alias.

        This method searches for a subcommand with the given `name`,
        and removes it from the current command. If `name` was an alias,
        only the alias is removed from the current command, not the subcommand
        the alias references. The alias is also removed from the `Subcommand`
        itself.

        Parameters
        ----------
        name : str
            The name of the subcommand to remove.

        Returns
        -------
        Subcommand
            The removed subcommand.
        None
            A subcommand named `name` does not exist.
        """
        if (command := self.all_subcommands.pop(name)) is None:
            return None

        if len(command.aliases) < 1:
            return command

        if name in command.aliases:
            command.aliases.remove(name)
        else:
            for alias in command.aliases:
                _ = self.all_subcommands.pop(alias, None)

        return command


@runtime_checkable
class SupportsOptions(Protocol):
    """A protocol that defines the common operations for command-line
    arguments enabling additional functionality through switches or flags.

    Attributes
    ----------
    all_options
    options
    """

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        """A collection of options for this argument."""
        raise NotImplementedError

    @property
    def options(self) -> Sequence[Option[Any]]:
        """A collection of options for this argument, excluding aliases."""
        return [v for k, v in self.all_options.items() if k == v.name]

    def add_option(self, option: Option[Any], /) -> None:
        """Register a new option.

        Parameters
        ----------
        option
            The option to add.

        Raises
        ------
        OptionAlreadyExistsError
            An option already exists with the same name (or alias).
        """
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
        """Unregister an option or alias.

        This method searches for an option with the given `name`, and removes
        it from the current command. If `name` was an alias, only the alias is
        removed from the current command, not the option the alias references.
        The alias is also removed from the `Option` itself.

        Parameters
        ----------
        name : str
            The name of the option to remove.

        Returns
        -------
        Option
            The removed option.
        None
            An option named `name` does not exist.
        """
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
class SupportsPositionalArguments(Protocol):
    @property
    def positional_arguments(self) -> MutableSequence[PositionalArgument[Any]]:
        raise NotImplementedError

    def add_positional_argument(
        self, argument: PositionalArgument[Any], /
    ) -> None:
        self.positional_arguments.append(argument)

    @overload
    def remove_positional_argument(
        self,
        name: str,
        /,
    ) -> PositionalArgument[Any] | None: ...

    @overload
    def remove_positional_argument(
        self,
        index: int,
        /,
    ) -> PositionalArgument[Any] | None: ...

    def remove_positional_argument(
        self,
        query: str | int,
        /,
    ) -> PositionalArgument[Any] | None:
        match query:
            case int():
                return self.positional_arguments.pop(query)
            case str():
                for index, argument in enumerate(self.positional_arguments):
                    if query != argument.name:
                        continue

                    return self.positional_arguments.pop(index)
            case _:
                raise TypeError(f"expected str or int, not {type(query)}")

        return None


@runtime_checkable
class SupportsConvert[T](Protocol):
    @property
    def target_type(self) -> Callable[[str], T]:
        """The type to convert to."""
        raise NotImplementedError

    @property
    def default_value(self) -> T:
        """An optional fallback value."""
        raise NotImplementedError

    def convert(self, argument: str, /) -> T:
        """Transform `argument` into `T`.

        Parameters
        ----------
        argument
            The value to convert.

        Raises
        ------
        TODO
        """

        return convert(
            argument=argument,
            converter=self.target_type,
            default_value=self.default_value,
        )


@runtime_checkable
class SupportsHelpMessage(Protocol):
    @property
    def usage(self) -> Usage:
        raise NotImplementedError

    def generate_help_message(self, fmt: HelpFormatter) -> str:
        raise NotImplementedError
