"""
Parser
------

This module implements the command-line argument parser. It converts the
command-line arguments into positional and keyword arguments and passes them
to the appropriate subcommand.

"""
from __future__ import annotations

import dataclasses
import importlib
import logging
import os
import sys
from typing import TYPE_CHECKING, final

from .commands import Command, SupportsCommands, add_command
from .groups import Group, accumulate_commands
from .help import Help, HelpFormatter
from .lexer import Lexer, TokenType
from .options import DefaultHelp, add_option
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import set as Set
    from typing import Any, Callable, Optional, Union

    from .lexer import Token
    from .options import Option

__all__ = [
    "ArgumentParser",
    "Extension",
]

_log = logging.getLogger(__name__)


class Extension:
    def __new__(cls) -> Extension:
        self = super().__new__(cls)
        # I want to leave __init__ alone so that subclasses don't have to
        # worry about calling super().__init__, but I also need to implement
        # the SupportsCommands protocol, so I'm doing it here instead.
        self.name = self.__class__.__name__
        self.all_commands = {}
        accumulate_commands(self)
        return self


@dataclasses.dataclass
class _Context:
    """Provides context to the various parser methods about the current
    state of the parser.

    Attributes
    ----------
    command : Union[:class:`Command`, :class:`SupportsCommands`]
        The command that is currently being invoked.
    positional : :class:`list`
        A list of positional arguments that have been parsed.
    keyword : :class:`dict`
        A mapping of keyword arguments that have been parsed.
    """

    command: Union[Command[Any], SupportsCommands]
    positional: List[Any] = dataclasses.field(default_factory=list)
    keyword: Dict[str, Any] = dataclasses.field(default_factory=dict)


@final
class ArgumentParser:
    """A command-line argument parser.

    This class is responsible for parsing the command-line arguments and
    passing them to the appropriate subcommand. This class is not meant to be
    subclassed directly. Instead, subclass :class:`.Group` and use the
    :func:`.add_command` to attach the group to the parser.

    Attributes
    ----------
    brief : :class:`str`
        A short description of the program.
    description : :class:`str`
        A longer description of the program.
    epilog : :class:`str`
        The text displayed at the bottom of the help message.
    program : :class:`str`
        The name of the program. Used in the USAGE section of the help message.
    all_commands : :class:`dict`
        A mapping of command names to command instances.
    options : :class:`dict`
        A mapping of option names to option instances.
    """

    def __init__(
        self,
        brief: str,
        *args: Any,
        description: Optional[str] = None,
        epilog: Optional[str] = None,
        program: str = os.path.basename(sys.argv[0]),
        **kwargs: Any,
    ) -> None:
        self.brief = brief
        self.description = description
        self.epilog = epilog
        self.name = program

        self.all_commands: Dict[str, Union[Command[Any], SupportsCommands]]
        self.all_commands = {}
        self.all_options: Dict[str, Option[Any]] = {}

        add_option(self, DefaultHelp)
        accumulate_commands(self)

    @property
    def commands(self) -> Set[Union[Command[Any], SupportsCommands]]:
        """A set of all commands that are attached to this parser."""
        # Exclude aliases while retaining the original order.
        return [v for k, v in self.all_commands.items() if k == v.name]

    @property
    def options(self) -> Set[Option[Any]]:
        """A set of all options that are attached to this parser."""
        # Exclude aliases while retaining the original order.
        return [v for k, v in self.all_options.items() if k == v.name]

    def display_help(self, *, fmt: HelpFormatter) -> None:
        """Display this help message and exit."""
        h = Help()
        h.add_line(self.brief)
        h.add_newline()

        if self.description is not None:
            node = h.add_section("DESCRIPTION")
            node.add_item(brief=self.description)

        usage = self.name

        assert self.options, "Parser should have at least the default help."
        options = " | ".join(f"--{option.name}" for option in self.options)
        usage += f" [{options}]"

        if self.commands:
            usage += " <COMMAND> [<ARGUMENTS>...]"

        h.add_section("USAGE", brief=usage)

        node = h.add_section("OPTIONS", skip_if_empty=True)

        for option in self.options:
            node.add_item(**option.help_info)

        node = h.add_section(
            "COMMANDS",
            brief="'*' indicates a COMMAND GROUP",
            skip_if_empty=True,
        )

        for command in self.commands:
            node.add_item(**command.help_info)

        if self.epilog:
            h.add_line(self.epilog) if self.epilog else None

        message = h.build()
        sys.stdout.write(message)

    def invoke(self, *args: Any, **kwargs: Any) -> None:
        return self.display_help(*args, **kwargs)

    def parse(
        self,
        args: List[str] = sys.argv,
        /,
        *,
        help_fmt: HelpFormatter = HelpFormatter(),
    ) -> None:
        """Parse the command-line arguments.

        Parameters
        ----------
        args : :class:`list`, optional
            The command-line arguments to parse. Defaults to :data:`sys.argv`.

        Other Parameters
        ----------------
        help_fmt : :class:`HelpFormatter`, optional
            The help formatter to use. Defaults to a :class:`.HelpFormatter`
            with default settings.
        """
        lexer = Lexer(args[1:])
        ctx = _Context(self)
        deferred: List[Token] = []

        for token in lexer:
            if token.is_option:
                deferred.append(token)

                try:
                    next_token = lexer.peek()
                except StopIteration:
                    next_token = None

                if next_token is None or next_token.is_option:
                    continue

                if next_token.is_argument:
                    deferred.append(next_token)
                    _ = next(lexer)

            elif token.is_argument:
                handle_argument_token(token, None, ctx)
            elif token.is_escape:
                continue
            elif token.is_stdin:
                raise NotImplementedError
            else:
                raise NotImplementedError

        handle_deferred_tokens(deferred, ctx)

        for option in ctx.command.all_options.values():
            option_name = option.as_snake_case
            if option_name in ctx.keyword or option.default is MISSING:
                continue

            ctx.keyword[option_name] = option.default

        for opt in ctx.keyword.keys():
            option = ctx.command.all_options[opt]
            option.validate_requires(ctx.keyword.keys())
            option.validate_conflicts(ctx.keyword.keys())

        if ctx.keyword.pop("help", False) or not lexer.args:
            ctx.command.display_help(fmt=help_fmt)
            return

        invoke_command(ctx, help_fmt)

    def extend(self, name: str, package: Optional[str] = None) -> None:
        """Add commands and groups from an extension file to this parser.

        Parameters
        ----------
        name : :class:`str`
            The name of the extension to add. This is a dot-separated path
            to the extension file.
        package : Optional[:class:`str`]
            The package to import from. Defaults to the current package.

        Examples
        --------
        Assume the following directory structure::

            ./my_package
            ├── extensions
            │   ├── __init__.py
            │   └── my_extension.py
            ├── __init__.py
            └── __main__.py

        >>> # my_extension.py
        >>> import clap
        >>>
        >>>
        >>> class MyExtension(clap.Extension):
        ...
        ...     @clap.group()
        ...     def my_group(self) -> None:
        ...         \"\"\"A short description of my_group.\"\"\"
        ...         pass
        ...
        ...     @my_group.command()
        ...     def my_command(self, foo: str, /) -> None:
        ...         \"\"\"A short description of my_command.
        ...
        ...         Parameters
        ...         ----------
        ...         foo : :class:`str`
        ...             A short description of foo.
        ...         \"\"\"
        ...         pass
        >>>
        >>>
        >>> def setup(parser: clap.ArgumentParser) -> None:
        ...     parser.add_extension(MyExtension())


        >>> # __main__.py
        >>> import sys
        >>>
        >>> import clap
        >>>
        >>> from .docs import url
        >>>
        >>>
        >>> def main() -> int:
        ...     parser = clap.ArgumentParser(
        ...         "A short description of my program.",
        ...         epilog=f"Documentation can be found at {url}.",
        ...     )
        """
        module = importlib.import_module(name, package=package)
        setup_func = getattr(module, "setup", None)

        if setup_func is None:
            raise AttributeError(
                f"extension '{name}' does not have a global 'setup' function"
            )

        setup_func(self)

    def add_extension(self, extension: Extension) -> None:
        """Add all commands from an extension to this parser.

        What makes an extension special is that they allow the user to extend
        the parser without having to subclass it or trying to jam everything
        into a single file. This is done by attaching the extension to the
        parser, but __self__ remains an instance of the extension class.

        Parameters
        ----------
        extension : :class:`Extension`
            The extension to add to this parser.

        Raises
        ------
        ValueError
            If the extension is already attached to a parser.
        """
        if not isinstance(extension, Extension):
            raise TypeError(
                "expected an Extension instance, not " f"{type(extension)!r}"
            )

        # add_command takes care of aliases, so filter out the aliases here.
        commands = [
            v for k, v in extension.all_commands.items() if k == v.name
        ]
        for command in commands:
            add_command(self, command)

    def add_command(
        self, command: Union[Command[Any], SupportsCommands]
    ) -> None:
        """Add a command to this parser.

        Parameters
        ----------
        command : Union[:class:`Command`, :class:`SupportsCommands`]
            The command to add to this parser.

        Raises
        ------
        ValueError
            If the command is already attached to a parser.
        """
        if isinstance(command, (Command, SupportsCommands)):
            add_command(self, command)
        else:
            raise TypeError(
                "expected a Command or SupportsCommands instance, "
                f"not {type(command)!r}"
            )

    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[..., Command[Any]]:
        def decorator(callback: Callable[..., Any]) -> Command[Any]:
            kwargs.setdefault("parent", self)
            c = Command(callback, *args, **kwargs)
            add_command(self, c)
            return c

        return decorator

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., Group]:
        def decorator(callback: Callable[..., Any]) -> Group:
            kwargs.setdefault("parent", self)
            g = Group(callback, *args, **kwargs)
            add_command(self, g)
            return g

        return decorator


def invoke_command(ctx: _Context, help_fmt: HelpFormatter) -> None:
    try:
        ctx.command.invoke(*ctx.positional, **ctx.keyword)
    except TypeError:  # argument-related error
        ctx.command.display_help(fmt=help_fmt)
    except Exception as exc:
        _log.exception(
            f"Failed to invoke command {ctx.command.name!r} with "
            f"positional arguments {ctx.positional!r} and "
            f"keyword arguments {ctx.keyword!r}: {exc}"
        )


def handle_deferred_tokens(deferred: List[Token], /, ctx: _Context) -> None:
    token_mapping = {
        TokenType.LONG_OPTION: handle_long_option_token,
        TokenType.SHORT_OPTION: handle_short_option_token,
        TokenType.ARGUMENT: handle_argument_token,
    }

    while deferred:
        token = deferred.pop(0)
        next_token = deferred[0] if deferred else None

        token_mapping[token.token_type](token, next_token, ctx)


def handle_long_option_token(
    token: Token,
    next_token: Optional[Token],
    ctx: _Context,
) -> None:
    flag, value = token.from_long_option()

    if token.as_snake_case not in ctx.command.all_options.keys():
        raise ValueError(f"invalid option: {token}")

    option = ctx.command.all_options[token.as_snake_case]

    if value == "":
        valid_next_token = next_token is not None and next_token.is_argument

        if option.target_type is bool:
            assert option.default is not MISSING
            value = str(not option.default)
        elif valid_next_token and option.n_args.maximum > 0:
            value = next_token.from_argument()
        else:
            value = ""

    converted_value = option.convert(value)
    ctx.keyword[option.as_snake_case] = converted_value


def handle_short_option_token(
    token: Token,
    next_token: Optional[Token],
    ctx: _Context,
) -> None:
    for flag, value in token.from_short_option():
        try:
            option = ctx.command.all_options[flag]
        except KeyError:
            raise ValueError(f"invalid option: {flag}")

        new_token_type = TokenType.LONG_OPTION
        new_value = "--" + option.as_kebab_case

        if value is not None:
            new_value += "=" + value

        new_token = Token(new_token_type, new_value)
        handle_long_option_token(new_token, next_token, ctx)


def handle_argument_token(
    token: Token,
    next_token: Optional[Token],
    ctx: _Context,
) -> None:
    value = token.from_argument()

    if isinstance(ctx.command, SupportsCommands):
        try:
            ctx.command = ctx.command.all_commands[value]
        except KeyError:
            raise ValueError(f"invalid command: {value}")

        return

    index = len(ctx.positional)

    try:
        argument = ctx.command.arguments[index]
    except IndexError:
        raise ValueError(f"too many arguments: {value}")

    converted_value = argument.convert(value)
    ctx.positional.append(converted_value)
