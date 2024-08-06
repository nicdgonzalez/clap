from __future__ import annotations

import importlib
import inspect
import logging
import sys
from os import path
from typing import TYPE_CHECKING, Optional, cast

from .abc import CallableArgument, HasCommands, HasOptions, HasPositionalArgs
from .arguments import DEFAULT_HELP
from .commands import (
    Command,
    Group,
    convert_function_parameters,
    inject_commands_from_members_into_self,
)
from .errors import ErrorMessage
from .help import HelpBuilder, HelpFormatter
from .parser import Parser
from .utils import MISSING, parse_docstring

if TYPE_CHECKING:
    from typing import Any, Callable, Self

    from .arguments import Option, Positional


__all__ = (
    "Extension",
    "Application",
    "Script",
    "parse_args",
    "script",
)

_log = logging.getLogger(__name__)


def parse_args(
    interface: Application | Script,
    args: list[str] = sys.argv,
    *,
    formatter: HelpFormatter = HelpFormatter(),
) -> Any:
    parser = Parser(args, command=interface)
    parsed_args = parser.parse()
    has_command = isinstance(parsed_args[-1].command, Command)

    for ctx in parsed_args:
        if ctx.kwargs.pop("help", False) or len(args) == 1:
            m = ctx.command.get_help_message(formatter=formatter)
            sys.stdout.write(m)
            return

        if (
            isinstance(ctx.command, HasCommands)
            and not ctx.command.invoke_without_command
            and not has_command
        ):
            continue

        try:
            result = ctx.command(*ctx.args, **ctx.kwargs)
        except ErrorMessage as exc:
            _log.error(f"error: {exc}")
        except Exception as exc:
            _log.exception(exc)
            return
        else:
            pass
    else:
        return result  # only return the result of the last call to ctx.command


class Extension(HasCommands):

    if TYPE_CHECKING:
        _name: str
        _commands: dict[str, HasCommands | CallableArgument]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        this = super().__new__(cls)
        this._name = this.__class__.__name__
        this._commands = {}
        inject_commands_from_members_into_self(this)
        return this

    @property
    def all_commands(self) -> dict[str, HasCommands | CallableArgument]:
        return self._commands

    @property
    def name(self) -> str:
        return self._name


class Application(HasCommands, HasOptions):

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
        self._commands: dict[str, HasCommands | CallableArgument] = {}
        self._options: dict[str, Option] = {}
        self._parent = cast(Optional[HasCommands], None)
        self.add_option(DEFAULT_HELP)
        inject_commands_from_members_into_self(self)

        self.__post_init__()

    def __post_init__(self) -> None:
        return

    def __call__(self, *args: Any, **kwargs: Any) -> None:
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

    @property
    def all_commands(self) -> dict[str, HasCommands | CallableArgument]:
        return self._commands

    @property
    def all_options(self) -> dict[str, Option]:
        return self._options

    @property
    def parent(self) -> Optional[HasCommands]:
        return self._parent

    @parent.setter
    def parent(self, value: Optional[HasCommands]) -> None:
        self._parent = value

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

    def command(self, *args: Any, **kwargs: Any) -> Callable[..., Command]:
        def decorator(callback: Callable[..., Any], /) -> Command:
            kwargs.setdefault("parent", self)
            c = Command.from_function(callback, *args, **kwargs)
            self.add_command(c)

            return c

        return decorator

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., Group]:
        def decorator(callback: Callable[..., Any], /) -> Group:
            kwargs.setdefault("parent", self)
            g = Group.from_function(callback, *args, **kwargs)
            self.add_command(g)

            return g

        return decorator

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


class Script(HasOptions, HasPositionalArgs):

    def __init__(
        self,
        callback: Callable[..., Any],
        /,
        name: str,
        brief: str,
        description: str,
        options: dict[str, Option],
        positionals: list[Positional],
        epilog: str = "Built using ndg.clap!",
    ) -> None:
        self._callback = callback
        self._name = name
        self._brief = brief
        self._description = description
        self._options = options
        self._positionals = positionals
        self._epilog = epilog
        self.add_option(DEFAULT_HELP)

    @classmethod
    def from_function(
        cls, callback: Callable[..., Any], /, **kwargs: Any
    ) -> Self:
        kwargs.setdefault("name", path.basename(sys.argv[0]))
        parsed_docs = parse_docstring(inspect.getdoc(callback) or "")
        kwargs.setdefault("brief", parsed_docs.pop("__brief__", ""))
        kwargs.setdefault("description", parsed_docs.pop("__desc__", ""))
        kwargs.setdefault("options", {})
        kwargs.setdefault("positionals", [])

        this = cls(callback, **kwargs)
        data = convert_function_parameters(callback, param_docs=parsed_docs)

        for option in data.options:
            this.add_option(option)

        for positional in data.positionals:
            this.add_positional(positional)

        return this

    @property
    def callback(self) -> Callable[..., Any]:
        return self._callback

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
    def all_options(self) -> dict[str, Option]:
        return self._options

    @property
    def all_positionals(self) -> list[Positional]:
        return self._positionals

    @property
    def epilog(self) -> str:
        return self._epilog

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._callback(*args, **kwargs)

    def get_help_message(self, formatter: HelpFormatter) -> str:
        builder = (
            HelpBuilder(formatter=formatter)
            .add_line(self.brief)
            .add_section("DESCRIPTION", skip_if_empty=True)
            .add_section("USAGE")
            .add_section("OPTIONS", skip_if_empty=True)
            .add_section("ARGUMENTS", skip_if_empty=True)
        )

        # description
        assert (section := builder.get_section("DESCRIPTION")) is not None

        if self.description:
            section.add_item(name="", brief=self.description)

        # usage
        usage = self.name
        options = " | ".join("--{}".format(opt.name) for opt in self.options)
        usage += " [{}]".format(options)

        for p in self.all_positionals:
            if p.default is MISSING:
                usage += " <{}>".format(p.name)
            else:
                usage += " [{}={!r}]".format(p.name, p.default)

        assert (section := builder.get_section("USAGE")) is not None
        section.add_item(name="", brief=usage)

        # options
        assert (section := builder.get_section("OPTIONS")) is not None
        for option in self.options:
            section.add_item(**option.help_info)

        # arguments
        assert (section := builder.get_section("ARGUMENTS")) is not None
        for positional in self.all_positionals:
            section.add_item(**positional.help_info)

        return builder.build()


def script(*args: Any, **kwargs: Any) -> Callable[..., Script]:
    def decorator(callback: Callable[..., Any], /) -> Script:
        return Script.from_function(callback, *args, **kwargs)

    return decorator
