"""
Parser
======

This module contains the parser for the command-line arguments.

Examples
--------
>>> from typing import Any, Annotated
>>>
>>> import clap
>>> from clap.metadata import Short, Conflicts
>>>
>>>
>>> class ExampleCLI(clap.Parser):
...     \"\"\"Represents a collection of commands for the Example CLI.\"\"\"
...
...     def __init__(self, *args: Any, **kwargs: Any) -> None:
...         super().__init__(
...             help="A command-line tool for managing servers.",
...             epilog="Thank you for using Example CLI!",
...             *args,
...             **kwargs,
...         )
...         # do normal object initialization stuff here:
...         self.foo = "bar"
...         self.baz = 69
...
...     @clap.command()
...     def start(
...         self,
...         ip: str,
...         port: int = 8080,
...         /,
...         *,
...         verbose: Annotated[bool, Short("v"), Conflicts("quiet")] = False,
...         quiet: Annotated[bool, Short("q"), Conflicts("verbose")] = False,
...     ) -> None:
...         \"\"\"Starts the specified server.
...
...         Parameters
...         ----------
...         ip : str
...             The IP address of the server to start.
...         port : int, default=25565
...             The port of the server to start.
...         verbose : bool, default=False
...             Whether to print verbose output.
...         \"\"\"
...         ...

"""
from __future__ import annotations

import os
import sys
from typing import Any, Iterable, ParamSpec, TypeVar

from .arguments import DefaultHelp, Option
from .commands import Command, Group
from .help import HelpBuilder, HelpFormatter
from .lexer import Lexer, Token, TokenType
from .utils import MISSING

__all__ = ("Parser",)

T = TypeVar("T")
P = ParamSpec("P")


class Parser:
    """Represents the parser for command-line arguments.

    Parameters
    ----------
    help : str
        The help message for the parser.
    epilog : str
        The epilog for the parser.

    Attributes
    ----------
    help : str
        The help message for the parser.
    epilog : str
        The epilog for the parser.
    program : str
        The name of the program.
    commands : dict[str, Command[Any]]
        The commands that the user can execute.
    options : dict[str, Option[Any]]
        The options that the user can pass to the parser.
    short_option_map : dict[str, str]
        A mapping of short option names to long option names.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.help = kwargs.pop("help", MISSING)
        self.epilog = kwargs.pop("epilog", MISSING)
        self.program = os.path.basename(sys.argv[0])
        self.options: dict[str, Option[Any]] = {}
        self.short_option_map: dict[str, str] = {}

        self.commands: dict[str, Command[Any] | Group] = {}
        for command in self.__class__.__dict__.values():
            if isinstance(command, (Command, Group)):
                command.parent = self
                self.commands[command.name] = command

        self.add_option(DefaultHelp)

    def add_command(self, command: Command[Any] | Group, /) -> None:
        """Adds a command to the parser.

        Parameters
        ----------
        command : Command[Any] | Group
            The command to add.
        """
        if not isinstance(command, (Command, Group)):
            raise TypeError(
                f"Expected a command or group, got {type(command).__name__}."
            )
        elif command.name in self.commands:
            raise ValueError(f"Command {command.name} already exists.")
        else:
            self.commands[command.name] = command

    def remove_command(self, name: str, /) -> None:
        """Removes a command from the parser.

        Parameters
        ----------
        name : str
            The name of the command to remove.
        """
        if name not in self.commands:
            raise ValueError(f"Command {name} does not exist.")
        del self.commands[name]

    def add_option(self, option: Option[Any], /) -> None:
        """Adds an option to the parser.

        Parameters
        ----------
        option : Option[Any]
            The option to add.
        """
        if option.short is not MISSING:
            if option.short in self.short_option_map:
                raise ValueError(
                    f"Short option {option.short} already exists for option "
                    f"{self.short_option_map[option.short]}. Cannot add "
                    f"option {option.name}."
                )
            self.short_option_map[option.short] = option.name

        if option.name in self.options:
            raise ValueError(f"Option {option.name} already exists.")
        self.options[option.name] = option

    def remove_option(self, name: str, /) -> None:
        """Removes an option from the parser.

        Parameters
        ----------
        name : str
            The name of the option to remove.
        """
        if name == "help":
            raise ValueError("The help option cannot be removed.")

        if name not in self.options:
            raise ValueError(f"Option {name} does not exist.")
        else:
            del self.options[name]

        for short, long in self.short_option_map.items():
            if long == name:
                del self.short_option_map[short]
                break

    def print_help(
        self,
        *,
        help_fmt: HelpFormatter = HelpFormatter(),
    ) -> None:
        """Prints the help message for the parser.

        Parameters
        ----------
        help_fmt : HelpFormatter, optional
            The help formatter to use. If not provided, the default formatter
            will be used.
        """
        builder = HelpBuilder(formatter=help_fmt)
        builder.add_line(self.help)

        usage = self.program
        if self.commands:
            usage += " <COMMAND> [OPTIONS] [ARGUMENTS]"
        else:
            # There should always be at least the "help" option.
            usage += " [OPTIONS]"
        builder.add_header("USAGE", usage)
        builder.add_line(
            "For more information on a specific command, use "
            "'<COMMAND> --help'."
        )

        builder.add_header("OPTIONS")
        for option in self.options.values():
            builder.add_item(option)

        builder.add_header("COMMANDS")
        for command in self.commands.values():
            builder.add_item(command)
        builder.placeholder = "No commands available."
        builder.flush_buffer()
        builder.placeholder = None

        if self.epilog is not MISSING:
            builder.add_newline()
            builder.add_line(self.epilog)

        sys.stdout.write(builder.build())

    def parse(
        self,
        argv: list[str] = sys.argv,
        /,
        *,
        help_fmt: HelpFormatter = HelpFormatter(),
    ) -> None:
        """Parses the command-line arguments.

        Parameters
        ----------
        argv : list[str], optional
            The command-line arguments to parse. If not provided, the arguments
            passed to the program will be used.
        """
        try:
            (args := argv.copy()).pop(0)
        except IndexError as e:
            raise ValueError("Expected at least the program name.") from e

        if len(args) < 1:
            self.print_help(help_fmt=help_fmt)
            return

        lexer = Lexer(args)
        cursor = lexer.cursor()
        deferred: list[Token] = []
        # For passing around context between various parts of the parser.
        ctx: dict[str, Any] = {
            "command": self,
            "arguments": [],
            "options": {},
        }

        for token in lexer.tokens(cursor, peek=False):
            match token.type:
                # All flags are deferred so that both `clap --help command`
                # and `clap command --help` are equivalent.
                case TokenType.LONG_OPTION:
                    deferred.append(token)
                case TokenType.SHORT_OPTION:
                    deferred.append(token)
                    # TODO: Handle options that take arguments.
                    # I think it would be easiest to have the Lexer take
                    # commands, options, and arguments as parameters and
                    # return the appropriate token type. This would require
                    # some changes to the Lexer, but it would make the parser
                    # much simpler.
                case TokenType.ARGUMENT:
                    self._parse_argument(token, ctx)
                case _:
                    raise ValueError(f"Invalid token type: {token.type}.")

        self._process_deferred(deferred, ctx)

        for option in ctx["command"].options.values():
            name = option.name.replace("-", "_")
            if name in ctx["options"] or option.default is MISSING:
                continue

            ctx["options"][name] = option.default

        if ctx["options"].pop("help", False) is True:
            ctx["command"].print_help(help_fmt=help_fmt)
            return

        ctx["command"](*ctx["arguments"], **ctx["options"])

    def _process_deferred(
        self,
        deferred: list[Token],
        ctx: dict[str, Any],
        /,
    ) -> None:
        """Processes deferred tokens.

        Parameters
        ----------
        deferred : list[Token]
            The list of deferred tokens.
        ctx : dict[str, Any]
            The context of the command.
        """
        while deferred:
            token = deferred.pop(0)
            next_token = (
                deferred[0]
                if deferred and token.type is TokenType.LONG_OPTION
                else None
            )

            match token.type:
                case TokenType.LONG_OPTION:
                    self._parse_option(token, ctx, next_token=next_token)
                case TokenType.SHORT_OPTION:
                    self._parse_short_option(token, ctx, next_token=next_token)
                case _:
                    raise ValueError(f"Invalid token type: {token.type}.")

    def _parse_option(
        self,
        token: Token,
        ctx: dict[str, Any],
        /,
        next_token: Token | None = None,
    ) -> None:
        """Processes an option.

        Parameters
        ----------
        token : Token
            The token to process.
        ctx : dict[str, Any]
            The context of the command.
        next_token : Token | None, optional
            The next token. This is used for options that take arguments.
        """
        assert token.type is TokenType.LONG_OPTION
        name = token.value.lstrip("-")
        value: Any = MISSING
        if "=" in name:
            name, value = name.split("=", maxsplit=1)
        command: Parser | Command[Any] | Group = ctx["command"]
        if name not in command.options:
            raise ValueError(f"Unknown option: {name}.")
        option = command.options[name]

        while value is MISSING:
            if option.cls is bool:
                value = True
            elif next_token is not None:
                if next_token.type is TokenType.ARGUMENT:
                    value = next_token.value
                else:
                    next_token = None
                    # value is still MISSING, so the loop will rerun
                    # and continue checking the remaining conditions.
            elif option.default is not MISSING:
                value = option.default
            else:
                raise ValueError(f"Option '{name}' requires an argument.")

        minimum, maximum = option.range
        if minimum > 1:
            value = value.split(",")
            if maximum is not None and len(value) > maximum:
                raise ValueError(
                    f"Option '{name}' takes up to ({maximum}) arguments, "
                    f"got {len(value)}."
                )
            elif len(value) < minimum:
                raise ValueError(
                    f"Option '{name}' takes at least ({minimum}) arguments, "
                    f"got {len(value)}."
                )

        name = name.replace("-", "_")
        ctx["options"][name] = (
            option.cls(value)
            if not isinstance(value, Iterable) or isinstance(value, str)
            else [option.cls(v) for v in value]
        )

    def _parse_short_option(
        self,
        token: Token,
        ctx: dict[str, Any],
        /,
        next_token: Token | None = None,
    ) -> None:
        """Processes a short option.

        Parameters
        ----------
        token : Token
            The token to process.
        ctx : dict[str, Any]
            The context of the command.
        next_token : Token | None, optional
            The next token. This is used for options that take arguments.
        """
        assert token.type is TokenType.SHORT_OPTION
        command: Parser | Command[Any] | Group = ctx["command"]
        name = token.value.lstrip("-")
        if name not in command.short_option_map:
            raise ValueError(f"Unknown short option: {name}.")
        long_name = command.short_option_map[name]
        self._parse_option(
            Token(TokenType.LONG_OPTION, long_name),
            ctx,
            next_token=next_token,
        )

    def _parse_argument(self, token: Token, ctx: dict[str, Any], /) -> None:
        """Parses an argument.

        Parameters
        ----------
        token : Token
            The token to parse.
        ctx : dict[str, Any]
            The context of the command.
        """
        assert token.type is TokenType.ARGUMENT
        command: Parser | Command[Any] | Group = ctx["command"]
        if isinstance(command, (Parser, Group)):
            try:
                command.commands[token.value]
            except KeyError:
                raise ValueError(f"Unknown command: {token.value}.")

            ctx["command"] = self.commands[token.value]
            return

        index = len(ctx["arguments"])
        try:
            argument = ctx["command"].arguments[index]
        except IndexError:
            cls = str
        else:
            cls = argument.cls
        finally:
            ctx["arguments"].append(cls(token.value))
