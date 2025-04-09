from __future__ import annotations

import inspect
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    MutableMapping,
    MutableSequence,
    get_args,
    get_origin,
    get_type_hints,
)

from . import attributes  # For use in match-case.
from .abc import SupportsArguments, SupportsOptions
from .argument import Argument
from .attributes import Short
from .docstring import Docstring, parse_doc
from .errors import InvalidCallbackError
from .help import Argument as Arg
from .help import HelpFormatter, HelpMessage, Item, Section, Text, Usage
from .option import DEFAULT_HELP, Option
from .sentinel import MISSING

if TYPE_CHECKING:
    from .abc import SupportsCommands


class Command[T](SupportsOptions, SupportsArguments):
    def __init__(
        self,
        *,
        callback: Callable[..., T],
        name: str | None = None,
        brief: str | None = None,
        description: str | None = None,
        aliases: MutableSequence[str] | None = None,
        arguments: MutableSequence[Argument[Any]] | None = None,
        options: MutableMapping[str, Option[Any]] | None = None,
        parent: SupportsCommands | None = None,
    ) -> None:
        """Represents a command-line argument that performs an action.

        Parameters
        ----------
        callback : callable
            The function that will handle the execution of this command.
        name : str, optional
            A unique identifier for the command. Defaults to `callback`'s name.
        brief : str, optional
            A one-line description of what the command does. Defaults to the
            "Short Summary" section of the function's docstring.
        description : str, optional
            A more detailed explanation of this command. Defaults to the
            "Extended Summary" section of the function's docstring.
        aliases : iterable, optional
            Alternative names that can be used to invoke this command.

        Returns
        -------
        Command
            A wrapper over the callback function with additional data for
            exposing the function to the command line.

        Other Parameters
        ----------------
        arguments : iterable, optional
            A collection of `Argument` objects. By default, this is generated
            based on the function's positional arguments.
        options : mapping, optional
            A collection of `Option` objects. By default, this is generated
            based on the function's keyword-only arguments.
        parent : SupportsCommands, optional
            The group this command belongs to. This is usually an instance of
            `Application` or `Group`.
        """
        if not callable(callback):
            raise InvalidCallbackError()

        self.callback = callback

        if name is None:
            assert hasattr(self.callback, "__name__")
            name = self.callback.__name__

        self.name = name

        parsed_doc = parse_doc(inspect.getdoc(self.callback))

        self.brief = brief or parsed_doc["short_summary"] or ""
        self.description = description or parsed_doc["extended_summary"] or ""
        self.aliases = aliases if aliases is not None else ()

        parsed_params = parse_parameters(
            fn=self.callback,
            doc=parsed_doc,
        )

        self._arguments = arguments or []

        if arguments is None:
            for argument in parsed_params[0]:
                self.add_argument(argument)

        self._options = options or {}

        if options is None:
            for option in parsed_params[1].values():
                self.add_option(option)

        self.parent = parent
        self.add_option(DEFAULT_HELP)

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    @property
    def arguments(self) -> MutableSequence[Argument[Any]]:
        return self._arguments

    @property
    def qualified_name(self) -> str:
        if self.parent is not None:
            assert hasattr(self.parent, "qualified_name")
            parent = self.parent.qualified_name

        return f"{parent} {self.name}"

    def __call__(self, *args: object, **kwargs: object) -> T:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)

    @property
    def usage(self) -> Usage:
        names = self.qualified_name.split(" ")
        assert len(names) >= 2  # Should be at least `<parent> <this_command>`
        program_name = names.pop(0)

        usage = (
            Usage(program_name)
            .add_argument(Arg(name=" ".join(names), required=None))
            .add_argument(Arg(name="options", required=False))
            .add_argument(Arg(name="--", required=False))
        )

        for argument in self.arguments:
            required = argument.default_value is not MISSING
            usage.add_argument(Arg(name=argument.name, required=required))

        return usage

    def generate_help_message(self, fmt: HelpFormatter, /) -> str:
        arguments = Section("Arguments")

        for argument in self.arguments:
            arguments.add_item(Item(name=argument.name, brief=argument.brief))

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
            .add(arguments)
            .add(options)
            .render(fmt=fmt)
        )


def is_method(fn: Callable[..., Any], /) -> bool:
    parameters = inspect.signature(obj=fn).parameters

    return hasattr(fn, "__self__") or (
        inspect.isfunction(fn)
        and "." in getattr(fn, "__qualname__", "")
        and parameters.get("self") is not None
    )


def parse_parameters(
    fn: Callable[..., Any],
    doc: Docstring,
) -> tuple[list[Argument[Any]], dict[str, Option[Any]]]:
    parameters = list(inspect.signature(fn).parameters.values())
    type_hints = get_type_hints(obj=fn, include_extras=True)

    if is_method(fn):
        # We don't need to expose the `self` parameter.
        _ = parameters.pop(0)

    arguments: list[Argument[Any]] = []
    options: dict[str, Option[Any]] = {}

    for parameter in parameters:
        name = parameter.name
        _, brief = (doc["parameters"] or {}).get(name) or ("", "")

        tp = type_hints.get(name)

        if get_origin(tp=tp) is Annotated:
            args = get_args(tp=tp)
            assert len(args) > 1, len(args)
            target_type = args[0]
        else:
            target_type = tp

        default_value = (
            parameter.default
            if parameter.default is not inspect.Parameter.empty
            else MISSING
        )

        match parameter.kind:
            case (
                inspect.Parameter.POSITIONAL_ONLY
                | inspect.Parameter.VAR_POSITIONAL
                | inspect.Parameter.POSITIONAL_OR_KEYWORD
            ):
                argument = Argument(
                    name=name,
                    brief=brief,
                    target_type=target_type or str,
                    default_value=default_value,
                )
                arguments.append(argument)
            case (
                inspect.Parameter.KEYWORD_ONLY | inspect.Parameter.VAR_KEYWORD
            ):
                short: Short | None = None

                if hasattr(tp, "__metadata__"):
                    metadata = getattr(tp, "__metadata__", ())

                    for attribute in metadata:
                        match attribute:
                            case attributes.Short:
                                # This is the type, not an instance.
                                short = Short(name[0])
                            case Short():
                                short = attribute
                            case _:
                                pass

                option = Option(
                    name=name,
                    brief=brief,
                    target_type=target_type or bool,
                    default_value=default_value,
                    short=short,
                )
                options[name] = option
            case _:
                raise AssertionError(f"unreachable: {parameter.kind}")

    return (arguments, options)
