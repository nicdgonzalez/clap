from __future__ import annotations

import inspect
import importlib
import logging
import sys
from os import path
from typing import TYPE_CHECKING, Protocol

from .abc import CallableArgument, HasCommands, HasOptions, HasPositionalArgs
from .arguments import DEFAULT_HELP
from .commands import Command, inject_commands_from_members_into_self, convert_function_parameters
from .help import HelpBuilder, HelpFormatter
from .parser import Parser
from .utils import MISSING, parse_docstring

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Optional, Callable, Union

    from typing_extensions import Self

    from .arguments import Option, Positional


__all__ = (
    "Extension",
    "Application",
    "Script",
    "parse_args",
)

_log = logging.getLogger(__name__)


def parse_args(
    interface: Union[Application, Script],
    args: List[str] = sys.argv,
    *,
    formatter: HelpFormatter = HelpFormatter(),
) -> Any:
    parser = Parser(args[1:], command=interface)  # type: ignore
    ctx = parser.parse()

    if ctx.kwargs.pop("help", False) is True:
        # display the help message
        m = ctx.command.get_help_message(formatter=formatter)
        sys.stdout.write(m)
        return

    try:
        return ctx.command(*ctx.args, **ctx.kwargs)
    except TypeError:  # argument-related error
        m = ctx.command.get_help_message(formatter=formatter)
        sys.stdout.write(m)
        return
    except Exception as exc:
        _log.exception(exc)


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
        self._commands: Dict[str, CallableArgument] = {}
        self._options: Dict[str, Option] = {}
        self.add_option(DEFAULT_HELP)
        inject_commands_from_members_into_self(self)

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


class Script(HasOptions, HasPositionalArgs):

    def __init__(
        self,
        callback: Callable[..., Any],
        /,
        name: str,
        brief: str,
        description: str,
        options: Dict[str, Option],
        positionals: List[Positional],
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
    def from_main(cls, callback: Callable[..., Any], /, **kwargs: Any) -> Self:
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
    def all_options(self) -> Dict[str, Option]:
        return self._options

    @property
    def all_positionals(self) -> List[Positional]:
        return self._positionals

    @property
    def epilog(self) -> str:
        return self._epilog

    def __call__(self, *args: Any, **kwargs: Any) -> int:
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