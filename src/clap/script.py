import inspect
import os
import sys
from typing import Any, Callable, MutableMapping, MutableSequence, Sequence

from .abc import Argument, SupportsOptions, SupportsPositionalArguments
from .docstring import parse_doc
from .help import Arg, HelpFormatter, HelpMessage, Item, Section, Text, Usage
from .option import DEFAULT_HELP, Option
from .parser import parse
from .positional import PositionalArgument
from .sentinel import MISSING
from .subcommand import parse_parameters

__all__ = ("Script",)


class Script[T](Argument, SupportsOptions, SupportsPositionalArguments):
    def __init__(
        self,
        *,
        callback: Callable[..., T],
        name: str = os.path.basename(sys.argv[0]),
        brief: str | None = None,
        description: str | None = None,
        after_help: str | None = None,
        positional_arguments: MutableSequence[PositionalArgument[Any]]
        | None = None,
        options: MutableMapping[str, Option[Any]] | None = None,
    ) -> None:
        self.callback = callback

        if name is None:
            assert hasattr(self.callback, "__name__")
            name = self.callback.__name__

        self._name = name

        parsed_doc = parse_doc(inspect.getdoc(self.callback))

        self._brief = brief or parsed_doc["short_summary"] or ""
        self.description = description or parsed_doc["extended_summary"] or ""
        self.after_help = after_help

        parsed_params = parse_parameters(
            fn=self.callback,
            doc=parsed_doc,
        )

        self._positional_arguments = positional_arguments or []

        if positional_arguments is None:
            for argument in parsed_params[0]:
                self.add_positional_argument(argument)

        self._options = options or {}

        if options is None:
            for option in parsed_params[1].values():
                self.add_option(option)

        self.add_option(DEFAULT_HELP)

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    @property
    def positional_arguments(self) -> MutableSequence[PositionalArgument[Any]]:
        return self._positional_arguments

    def __call__(self, *args: object, **kwargs: object) -> T:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)

    @property
    def usage(self) -> Usage:
        usage = (
            Usage(self.name)
            .add_argument(Arg(name="options", required=False))
            .add_argument(Arg(name="--", required=False))
        )

        for argument in self.positional_arguments:
            required = argument.default_value is MISSING
            usage.add_argument(Arg(name=argument.name, required=required))

        return usage

    def generate_help_message(self, fmt: HelpFormatter, /) -> str:
        arguments = Section("Arguments")

        for argument in self.positional_arguments:
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

    def run(
        self,
        input: Sequence[str] = sys.argv[slice(1, None, 1)],
        *,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> Any:
        return parse(self, input=input, formatter=formatter)
