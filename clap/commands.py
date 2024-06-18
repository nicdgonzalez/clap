from __future__ import annotations

import dataclasses
import inspect
import logging
from typing import TYPE_CHECKING, get_type_hints

from .abc import (
    CallableArgument,
    HasCommands,
    HasOptions,
    HasPositionalArgs,
    ParameterizedArgument,
)
from .arguments import DEFAULT_HELP, Option, Positional
from .help import HelpBuilder, HelpFormatter
from .utils import MISSING, parse_docstring

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from builtins import type as Type
    from typing import Any, Callable, Optional

    from typing_extensions import Self

__all__ = ("Command", "command", "Group", "group")

_log = logging.getLogger(__name__)


def inject_commands_from_members_into_self(obj: HasCommands, /) -> None:
    members = tuple(obj.__class__.__dict__.values())
    for command in members:
        if not isinstance(command, CallableArgument):
            continue

        if isinstance(obj, HasCommands):
            command.parent = obj

        # Decorators on class methods wrap around the unbound method;
        # we need to set the `__self__` attribute manually
        if not hasattr(command.callback, "__self__"):
            setattr(command.callback, "__self__", obj)

        obj.add_command(command)


@dataclasses.dataclass
class CommandParameters:
    options: List[Option] = dataclasses.field(default_factory=list)
    positionals: List[Positional] = dataclasses.field(default_factory=list)
    mapping: Dict[Type[Any], List[ParameterizedArgument]] = dataclasses.field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        default_mapping = {
            Option: self.options,
            Positional: self.positionals,
        }
        self.mapping.update(default_mapping)  # type: ignore


def is_method_with_self(fn: Callable[..., Any], /) -> bool:
    """A helper function for checking whether a callable is an instance
    method, or an unbound method with `self` as the first parameter.

    Parameters
    ----------
    fn: :class:`Callable[..., Any]`
        The function to check.

    Returns
    -------
    :class:`bool` Whether the function is a method with `self`.
    """
    parameters = inspect.signature(fn).parameters

    return hasattr(fn, "__self__") or (
        inspect.isfunction(fn)
        and "." in getattr(fn, "__qualname__", "")
        and parameters.get("self") is not None
    )


PARAMETER_KIND_MAP: Dict[Any, Type[ParameterizedArgument]] = {
    inspect.Parameter.POSITIONAL_ONLY: Positional,
    inspect.Parameter.VAR_POSITIONAL: Positional,
    inspect.Parameter.POSITIONAL_OR_KEYWORD: Positional,
    inspect.Parameter.KEYWORD_ONLY: Option,
    inspect.Parameter.VAR_KEYWORD: Option,
}


def convert_function_parameters(
    fn: Callable[..., Any],
    *,
    param_docs: Dict[str, str] = {},
    ctx: Optional[CommandParameters] = None,
) -> CommandParameters:
    parameters = [_ for _ in inspect.signature(fn).parameters.values()]

    if is_method_with_self(fn):
        _ = parameters.pop(0)

    parameter_types = get_type_hints(fn, include_extras=True)
    ctx = ctx or CommandParameters()

    for parameter in parameters:
        t = PARAMETER_KIND_MAP[parameter.kind]

        obj = t.from_parameter(
            parameter,
            brief=param_docs.get(parameter.name, ""),
            target_type=parameter_types.get(parameter.name, str),
        )

        ctx.mapping[type(obj)].append(obj)

    return ctx


class Command(HasOptions, HasPositionalArgs):

    def __init__(
        self,
        callback: Callable[..., Any],
        /,
        name: str,
        brief: str,
        description: str,
        aliases: List[str],
        options: Dict[str, Option],
        positionals: List[Positional],
        parent: Optional[HasCommands],
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")

        self._callback = callback
        self._name = name
        self._brief = brief
        self._description = description
        self._aliases = aliases
        self._options = options
        self._positionals = positionals
        self._parent = parent
        self.add_option(DEFAULT_HELP)

    @classmethod
    def from_function(
        cls,
        callback: Callable[..., Any],
        /,
        **kwargs: Any,
    ) -> Self:
        if not callable(callback):
            raise TypeError("callback must be callable")

        kwargs.setdefault("name", callback.__name__)
        parsed_docs = parse_docstring(inspect.getdoc(callback) or "")
        kwargs.setdefault("brief", parsed_docs.pop("__brief__", ""))
        kwargs.setdefault("description", parsed_docs.pop("__desc__", ""))
        kwargs.setdefault("aliases", [])
        kwargs.setdefault("options", {})
        kwargs.setdefault("positionals", [])
        kwargs.setdefault("parent", None)

        this = cls(callback, **kwargs)
        data = convert_function_parameters(callback, param_docs=parsed_docs)

        for option in data.options:
            this.add_option(option)

        for positional in data.positionals:
            this.add_positional(positional)

        return this

    @property
    def all_options(self) -> Dict[str, Option]:
        return self._options

    @property
    def all_positionals(self) -> List[Positional]:
        return self._positionals

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
    def aliases(self) -> List[str]:
        return self._aliases

    @property
    def parent(self) -> Optional[HasCommands]:
        return self._parent

    @parent.setter
    def parent(self, value: HasCommands) -> None:
        self._parent = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)

    def get_help_message(self, formatter: HelpFormatter) -> str:
        builder = (
            HelpBuilder(formatter=formatter)
            .add_line(self.brief)
            .add_section("DESCRIPTION", skip_if_empty=True)
            .add_section("USAGE")
            .add_section("ALIASES", skip_if_empty=True)
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

        # aliases
        assert (section := builder.get_section("ALIASES")) is not None
        if self.aliases:
            section.add_item(name="", brief=", ".join(self.aliases))

        # options
        assert (section := builder.get_section("OPTIONS")) is not None
        for option in self.options:
            section.add_item(**option.help_info)

        # arguments
        assert (section := builder.get_section("ARGUMENTS")) is not None
        for positional in self.all_positionals:
            section.add_item(**positional.help_info)

        return builder.build()


def command(*args: Any, **kwargs: Any) -> Callable[..., Command]:

    def decorator(fn: Callable[..., Any], /) -> Command:
        if isinstance(fn, Command):
            raise TypeError("function is already a Command")

        return Command.from_function(fn, *args, **kwargs)

    return decorator


class Group(HasCommands, HasOptions):

    def __init__(
        self,
        callback: Callable[..., Any],
        /,
        name: str,
        brief: str,
        description: str,
        aliases: List[str],
        commands: Dict[str, CallableArgument],
        options: Dict[str, Option],
        parent: Optional[HasCommands],
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")

        self._callback = callback
        self._name = name
        self._brief = brief
        self._description = description
        self._aliases = aliases
        self._commands = commands
        self._options = options
        self._parent = parent
        inject_commands_from_members_into_self(self)
        self.add_option(DEFAULT_HELP)

    @classmethod
    def from_function(
        cls,
        callback: Callable[..., Any],
        /,
        **kwargs: Any,
    ) -> Self:
        if not callable(callback):
            raise TypeError("callback must be callable")

        kwargs.setdefault("name", callback.__name__)
        parsed_docs = parse_docstring(inspect.getdoc(callback) or "")
        kwargs.setdefault("brief", parsed_docs.get("__brief__", ""))
        kwargs.setdefault("description", parsed_docs.get("__desc__", ""))
        kwargs.setdefault("aliases", [])
        kwargs.setdefault("commands", {})
        kwargs.setdefault("options", {})
        kwargs.setdefault("parent", None)

        this = cls(callback, **kwargs)
        data = convert_function_parameters(callback, param_docs=parsed_docs)

        if len(data.positionals) > 1:
            raise TypeError("groups can not have positional arguments")

        for option in data.options:
            this.add_option(option)

        return this

    @property
    def all_commands(self) -> Dict[str, CallableArgument]:
        return self._commands

    @property
    def all_options(self) -> Dict[str, Option]:
        return self._options

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
    def aliases(self) -> List[str]:
        return self._aliases

    @property
    def parent(self) -> Optional[HasCommands]:
        return self._parent

    @parent.setter
    def parent(self, value: HasCommands) -> None:
        if not isinstance(value, HasCommands):
            raise TypeError("value does not satisfy the HasCommands protocol")

        self._parent = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)

    def command(self, *args: Any, **kwargs: Any) -> Callable[..., Command]:
        def decorator(fn: Callable[..., Any], /) -> Command:
            kwargs.setdefault("parent", self)
            c = Command.from_function(fn, *args, **kwargs)
            self.add_command(c)
            return c

        return decorator

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., Group]:
        def decorator(fn: Callable[..., Any], /) -> Group:
            kwargs.setdefault("parent", self)
            g = Group.from_function(fn, *args, **kwargs)
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


def group(*args: Any, **kwargs: Any) -> Callable[..., Group]:

    def decorator(fn: Callable[..., Any], /) -> Group:
        if isinstance(fn, Group):
            raise TypeError("function is already a Group")

        return Group.from_function(fn, *args, **kwargs)

    return decorator
