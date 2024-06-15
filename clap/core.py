from __future__ import annotations

import importlib
import sys
from os import path
from typing import TYPE_CHECKING, Callable, cast

from .abc import CallableArgument, HasCommands, HasOptions, HasPositionalArgs
from .arguments import DEFAULT_HELP
from .commands import Command, inject_commands_from_members_into_self
from .help import HelpBuilder, HelpFormatter
from .parser import Parser

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Optional

    from typing_extensions import Self

    from .arguments import Option, Positional


__all__ = (
    "Extension",
    "Application",
    "Script",
)


class Extension(HasCommands):

    if TYPE_CHECKING:
        _name: str
        _commands: Dict[str, CallableArgument]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        this = super().__new__(cls)
        this._name = this.__class__.__name__
        this._commands = {}
        inject_commands_from_members_into_self(this)
        return this

    @property
    def all_commands(self) -> Dict[str, CallableArgument]:
        return self._commands

    @property
    def name(self) -> str:
        return self._name


class ParserBase:

    def __init__(
        self,
        *,
        name: str = path.basename(sys.argv[0]),
        brief: str = "",
        description: str = "",
        epilog: str = "Built using ndg.clap!",
    ) -> None:
        self._name = name
        self._brief = brief
        self._description = description
        self._epilog = epilog
        self.__post_init__()

    def __post_init__(self) -> None:
        return

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def description(self) -> str:
        return self._description

    @property
    def epilog(self) -> str:
        return self._epilog

    def parse_args(
        self,
        args: List[str] = sys.argv,
        /,
        *,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> None:
        assert type(self) is not ParserBase, "do not use ParserBase directly"
        parser = Parser(args[1:], command=self)  # type: ignore
        ctx = parser.parse()

        # check if the user used the --help option
        if ctx.kwargs.pop("help", False) is True:
            # display the help message
            m = ctx.command.get_help_message(formatter=formatter)
            sys.stdout.write(m)
            return

        try:
            ctx.command(*ctx.args, **ctx.kwargs)
        except TypeError:  # argument-related error
            raise NotImplementedError
        except Exception as exc:
            raise NotImplementedError from exc


class Application(ParserBase, HasCommands, HasOptions):

    def __post_init__(self) -> None:
        self._commands: Dict[str, CallableArgument] = {}
        self._options: Dict[str, Option] = {}
        self.add_option(DEFAULT_HELP)
        inject_commands_from_members_into_self(self)

    @property
    def all_commands(self) -> Dict[str, CallableArgument]:
        return self._commands

    @property
    def all_options(self) -> Dict[str, Option]:
        return self._options

    def extend(self, name: str, package: Optional[str] = None) -> None:
        module = importlib.import_module(name, package=package)
        setup_fn = getattr(module, "setup", None)

        if setup_fn is None:
            raise AttributeError(
                "module {!r} missing global 'setup' function".format(name)
            )

        _ = setup_fn(self)

    def add_extension(self, extension: Extension, /) -> None:
        for command in extension.commands:
            self.add_command(command)

    def get_help_message(self, formatter: HelpFormatter) -> str:
        builder = (
            HelpBuilder(formatter=formatter)
            .add_line(self.brief)
            .add_section("DESCRIPTION", skip_if_empty=True)
            .add_section("USAGE")
            .add_section("OPTIONS", skip_if_empty=True)
            .add_section("COMMANDS", skip_if_empty=True)
            .add_line(self.epilog)
        )

        # description
        assert (section := builder.get_section("DESCRIPTION")) is not None

        if self.description:
            section.add_item(name="", brief=self.description)

        # usage
        usage = self.name
        options = " | ".join("--{}".format(opt.name) for opt in self.options)
        usage += " [{}]".format(options)

        if self.commands:
            usage += " <command> [<args>...]"

        assert (section := builder.get_section("USAGE")) is not None
        section.add_item(name="", brief=usage)

        # options
        assert (section := builder.get_section("OPTIONS")) is not None
        for option in self.options:
            section.add_item(**option.help_info)

        # commands
        assert (section := builder.get_section("COMMANDS")) is not None
        for command in self.commands:
            section.add_item(**command.help_info)

        return builder.build()


class Script(ParserBase, HasOptions, HasPositionalArgs):

    def __post_init__(self) -> None:
        self._positionals: List[Positional] = []
        self._options: Dict[str, Option] = {}
        self.add_option(DEFAULT_HELP)

    @property
    def all_options(self) -> Dict[str, Option]:
        return self._options

    @property
    def all_positionals(self) -> List[Positional]:
        return self._positionals

    def main(self, *args: Any, **kwargs: Any) -> Callable[..., int]:
        def decorator(fn: Callable[..., int], /) -> int:
            return cast(int, Command.from_function(fn)(*args, **kwargs))

        return decorator

    def get_help_message(self, formatter: HelpFormatter) -> str:
        # TODO: steal help message from Command
        raise NotImplementedError
