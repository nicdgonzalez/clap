import inspect
import os
import sys
from typing import Any, Callable, MutableMapping, MutableSequence, Sequence

from .abc import (
    Argument,
    SupportsHelpMessage,
    SupportsOptions,
    SupportsPositionalArguments,
)
from .docstring import parse_doc
from .help import HelpFormatter, HelpMessage, Text
from .option import DEFAULT_HELP, Option
from .parser import parse
from .positional import PositionalArgument
from .subcommand import _parse_parameters

__all__ = ("Script",)


# TODO: Documentation.
class Script[T](
    Argument, SupportsOptions, SupportsPositionalArguments, SupportsHelpMessage
):
    def __init__(
        self,
        *,
        callback: Callable[..., T],
        name: str = os.path.basename(sys.argv[0]),
        brief: str = "",
        description: str = "",
        after_help: str = "",
        positional_arguments: MutableSequence[PositionalArgument[Any]]
        | None = None,
        options: MutableMapping[str, Option[Any]] | None = None,
    ) -> None:
        self.callback = callback

        if name == "":
            assert hasattr(self.callback, "__name__")
            name = self.callback.__name__
        self._name = name

        parsed_doc = parse_doc(inspect.getdoc(self.callback))

        if brief == "":
            brief = parsed_doc["short_summary"] or ""
        self._brief = brief

        if description == "":
            description = parsed_doc["extended_summary"] or ""
        self._description = description

        self.after_help = after_help

        parsed_params = _parse_parameters(
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
    def qualified_name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def description(self) -> str:
        return self._description

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    @property
    def positional_arguments(self) -> MutableSequence[PositionalArgument[Any]]:
        return self._positional_arguments

    def __call__(self, *args: object, **kwargs: object) -> T:
        # I don't think it makes sense for the main function to be a method...
        #
        # if hasattr(self.callback, "__self__"):
        #     return self.callback(self.callback.__self__, *args, **kwargs)
        # else:
        #     return self.callback(*args, **kwargs)
        return self.callback(*args, **kwargs)

    def get_help_message(self) -> HelpMessage:
        help_message = SupportsHelpMessage.get_help_message(self)
        return help_message.add(Text(self.after_help))

    def run(
        self,
        input: Sequence[str] = sys.argv[slice(1, None, 1)],
        *,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> Any:
        return parse(self, input=input, formatter=formatter)
