import functools
import os
import sys
from typing import Callable, Iterable, Mapping

from .argument import Argument
from .command import Command
from .errors import CommandRegistrationError
from .option import Option
from .parser import parse


class Application:
    def __init__(
        self,
        *,
        name: str = os.path.basename(sys.argv[0]),
        brief: str = "",
        description: str = "",
        after_help: str = "",
    ) -> None:
        self.name = name
        self.brief = brief
        self.description = description
        self.after_help = after_help

        self.commands: dict[str, Command] = {}
        self.options: dict[str, Option] = {}

    def command(
        self,
        name: str = "",
        brief: str = "",
        description: str = "",
        aliases: Iterable[str] = (),
        arguments: Iterable[Argument] = (),
        options: Mapping[str, Option] = {},
    ) -> Callable[[Callable[..., None]], Command]:
        """A convenience decorator to convert a function into a
        [`Command`][clap.Command], and register it onto the application.

        Parameters
        ----------
        name : str, optional
            An identifier for the command. Defaults to the function name.
        brief : str, optional
            A short description of what the command does. Defaults to the first
            line of the function's docstring.
        description : str, optional
            A longer description explaining the command. Defaults to the first
            paragraph below the brief of the function's docstring.
        aliases : iterable, optional
            A collection of alternative identifiers that can be used to call
            this command.

        Other Parameters
        ----------------
        arguments : iterable, optional
            A collection of `Argument` objects. By default, this is generated
            based on the function's positional arguments.
        options : mapping, optional
            A collection of `Option` objects. By default, this is generated
            based on the function's keyword arguments.

        Returns
        -------
        callable
            The inner function wrapped in a `Command` object.
        """

        def wrapper(callback: Callable[..., None]) -> Command:
            command = Command(
                callback=callback,
                name=name,
                brief=brief,
                description=description,
                aliases=aliases,
                arguments=arguments,
                options=options,
            )
            self.add_command(command)
            return command

        return wrapper

    def add_command(self, command: Command) -> None:
        if command.name in self.commands.keys():
            raise CommandRegistrationError(
                f"command already exists: {command.name}"
            )

        self.commands[command.name] = command

    def run(
        self,
        input: Iterable[str] = sys.argv[slice(1, None, 1)],
    ) -> None:
        result = parse(self, input=input)
        print(result)
