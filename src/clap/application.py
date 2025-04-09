import os
import sys
import textwrap
from typing import Any, Callable, MutableMapping, Sequence

from .abc import SupportsCommands, SupportsHelpMessage, SupportsOptions
from .command import Command
from .errors import (
    ArgumentError,
    CommandAlreadyExistsError,
    OptionAlreadyExistsError,
)
from .help import (
    Argument,
    HelpFormatter,
    HelpMessage,
    Item,
    Section,
    Text,
    Usage,
)
from .option import DEFAULT_HELP, Option
from .parser import Parser


class Application(SupportsOptions, SupportsCommands):
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

        self._commands: dict[str, Command[Any]] = {}
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
    def all_commands(self) -> MutableMapping[str, Command[Any]]:
        return self._commands

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        help_message = self.generate_help_message(HelpFormatter())
        print(help_message)

    def command[T, **P](
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, T]], Command[T]]:
        """Convert a function into a [`Command`][clap.command.Command], and
        register it to the application.

        Returns
        -------
        callable
            The inner function wrapped in a `Command` object.

        See Also
        --------
        [Command][clap.command.Command] : For valid arguments to this function.
        """

        kwargs.setdefault("parent", self)

        def wrapper(callback: Callable[P, T]) -> Command[T]:
            command = Command(callback=callback, **kwargs)
            self.add_command(command)
            return command

        return wrapper

    def add_command(self, command: Command[Any]) -> None:
        if command.name in self.all_commands.keys():
            raise CommandAlreadyExistsError(self, command.name)

        self.all_commands[command.name] = command

    def add_option(self, option: Option[Any]) -> None:
        if option.name in self.all_options.keys():
            raise OptionAlreadyExistsError(self, option.name)

        self.all_options[option.name] = option

    def run(
        self,
        input: Sequence[str] = sys.argv[slice(1, None, 1)],
        *,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> Any:
        parser = Parser(app=self)

        try:
            results = parser.parse(input=input)
        except ArgumentError as exc:
            print(f"\033[31merror\033[39m: {exc}", file=sys.stderr)
            sys.exit(1)

        ends_with_command = isinstance(results[-1].command, Command)

        assert len(results) > 0, len(results)
        for result in results:
            if result.kwargs.pop("help", False):
                assert isinstance(result.command, SupportsHelpMessage)
                help_message = result.command.generate_help_message(formatter)
                print(help_message)
                return None

            if (
                isinstance(result.command, SupportsCommands)
                and not result.command.invoke_without_command
                and ends_with_command
            ):
                continue

            try:
                assert callable(result.command)
                retval: Any = result.command(*result.args, **result.kwargs)
            except TypeError:  # TODO: Throw a custom error instead.
                assert isinstance(result.command, SupportsHelpMessage)
                usage = result.command.usage.render(formatter)
                print(usage, file=sys.stderr)
                sys.exit(1)

        return retval

    @property
    def usage(self) -> Usage:
        return (
            Usage(self.name)
            .add_argument(Argument(name="options", required=False))
            .add_argument(Argument(name="--", required=False))
            .add_argument(Argument(name="command", required=True))
        )

    def generate_help_message(self, fmt: HelpFormatter, /) -> str:
        commands = Section("Commands")

        for command in self.commands:
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
