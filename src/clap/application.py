import os
import sys
import textwrap
from typing import Any, Callable, MutableMapping, Sequence

from .abc import Argument, SupportsOptions, SupportsSubcommands
from .group import Group
from .help import Arg, HelpFormatter, HelpMessage, Item, Section, Text, Usage
from .option import DEFAULT_HELP, Option
from .parser import parse
from .sentinel import MISSING
from .subcommand import Subcommand


class Application(Argument, SupportsOptions, SupportsSubcommands):
    def __init__(
        self,
        *,
        name: str = os.path.basename(sys.argv[0]),
        brief: str = "",
        description: str = "",
        after_help: str = "",
    ) -> None:
        self._name = name.strip()
        self._brief = brief.strip()
        self.description = textwrap.dedent(description).strip()
        self.after_help = after_help.strip()

        self._subcommands: dict[str, Group[Any] | Subcommand[Any]] = {}
        self._options: dict[str, Option[Any]] = {}
        self.add_option(DEFAULT_HELP)

    @property
    def name(self) -> str:
        return self._name

    @property
    def qualified_name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def all_subcommands(
        self,
    ) -> MutableMapping[str, Group[Any] | Subcommand[Any]]:
        return self._subcommands

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        help_message = self.generate_help_message(HelpFormatter())
        print(help_message)

    def subcommand[T, **P](
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, T]], Subcommand[T]]:
        """A convenience decorator to transform a function into a
        [`Subcommand`][clap.subcommand.Subcommand] and register it onto
        the application.

        Returns
        -------
        callable
            The inner function wrapped in a `Subcommand` object.

        See Also
        --------
        [Subcommand][clap.subcommand.Subcommand] : For valid arguments.
        """

        kwargs.setdefault("parent", self)

        def wrapper(callback: Callable[P, T]) -> Subcommand[T]:
            command = Subcommand(callback=callback, **kwargs)
            self.add_subcommand(command)
            return command

        return wrapper

    def group[T, **P](
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, T]], Group[T]]:
        """A convenience decorator to transform a function into a
        [`Group`][clap.group.Group] and register it onto
        the application.

        Returns
        -------
        callable
            The inner function wrapped in a `Group` object.

        See Also
        --------
        [Group][clap.group.Group] : For valid arguments.
        """

        kwargs.setdefault("parent", self)

        def wrapper(callback: Callable[P, T]) -> Group[T]:
            group = Group(callback=callback, **kwargs)
            self.add_subcommand(group)
            return group

        return wrapper

    @property
    def usage(self) -> Usage:
        usage = Usage(self.name)

        for option in self.options:
            if option.default_value is MISSING:
                usage.add_argument(Arg(name=f"--{option.name}", required=None))
                usage.add_argument(Arg(name="value", required=True))

        usage.add_argument(Arg(name="options", required=False))
        usage.add_argument(Arg(name="--", required=False))
        usage.add_argument(Arg(name="command", required=True))

        return usage

    def generate_help_message(self, fmt: HelpFormatter, /) -> str:
        commands = Section("Commands")

        for command in self.subcommands:
            commands.add_item(Item(name=command.name, brief=command.brief))

        options = Section("Options")

        for option in self.options:
            name = f"--{option.name}"

            if option.short is not None:
                name = f"-{option.short}, {name}"
            else:
                name = f"    {name}"

            options.add_item(Item(name=name, brief=option.brief))

        return (
            HelpMessage()
            .add(Text(self.brief))
            .add(Text(self.description))
            .add(self.usage)
            .add(commands)
            .add(options)
            .add(Text(self.after_help))
            .render(fmt=fmt)
        )

    def run(
        self,
        input: Sequence[str] = sys.argv[slice(1, None, 1)],
        *,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> Any:
        return parse(self, input=input, formatter=formatter)
