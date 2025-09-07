from __future__ import annotations

import inspect
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    MutableMapping,
    MutableSequence,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from . import attributes
from .abc import (
    Argument,
    SupportsHelpMessage,
    SupportsOptions,
    SupportsPositionalArguments,
)
from .attributes import MetaVar, Rename, Short
from .docstring import Docstring, parse_doc
from .option import DEFAULT_HELP, Option
from .positional import PositionalArgument
from .sentinel import MISSING
from .util import kebab_case

if TYPE_CHECKING:
    from .abc import SupportsSubcommands

T = TypeVar("T")


def _is_method_with_self(fn: Callable[..., Any], /) -> bool:
    parameters = inspect.signature(obj=fn).parameters

    return hasattr(fn, "__self__") or (
        inspect.isfunction(fn)
        and "." in getattr(fn, "__qualname__", "")
        and parameters.get("self") is not None
    )


def _parse_parameters(
    fn: Callable[..., Any],
    doc: Docstring,
) -> tuple[list[PositionalArgument[Any]], dict[str, Option[Any]]]:
    parameters = list(inspect.signature(fn).parameters.values())
    type_hints = get_type_hints(obj=fn, include_extras=True)

    if _is_method_with_self(fn):
        # We don't need to expose the `self` parameter to the command line.
        _ = parameters.pop(0)

    arguments: list[PositionalArgument[Any]] = []
    options: dict[str, Option[Any]] = {}

    # Merge the "Parameters" and "Other Parameters" sections.
    summaries = doc["parameters"] or {}
    summaries.update(**(doc["other_parameters"] or {}))

    for parameter in parameters:
        name = parameter.name
        _, brief = summaries.get(name) or ("", "")

        tp = type_hints.get(name) or str

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

        metavar: MetaVar | None = None

        match parameter.kind:
            case (
                inspect.Parameter.POSITIONAL_ONLY
                | inspect.Parameter.POSITIONAL_OR_KEYWORD
            ):
                if hasattr(tp, "__metadata__"):
                    metadata = getattr(tp, "__metadata__", ())

                    for attribute in metadata:
                        match attribute:
                            case Rename():
                                name = str(attribute)
                            case MetaVar():
                                metavar = attribute
                            case _:
                                pass

                argument = PositionalArgument(
                    name=name,
                    brief=brief,
                    metavar=metavar or MetaVar(name),
                    target_type=target_type,
                    default_value=default_value,
                )
                arguments.append(argument)
            case inspect.Parameter.VAR_POSITIONAL:
                # Maybe this can work as a catch-all? I'm not sure how
                # intuitive this would be or what use-cases it would have...
                # I have to think about it some more.
                #
                # The alternative I think is to have a MutableSequence
                # (e.g., list) type that let's you capture a range of values?
                # This way you have more control over what you're capturing...
                raise NotImplementedError("not implemented yet")
            case inspect.Parameter.KEYWORD_ONLY:
                short: Short | None = None
                rename: Rename | None = None

                if hasattr(tp, "__metadata__"):
                    metadata = getattr(tp, "__metadata__", ())

                    for attribute in metadata:
                        match attribute:
                            case attributes.Short:
                                short = Short(name[0])
                            case Short():
                                short = attribute
                            case Rename():
                                rename = attribute
                            case MetaVar():
                                metavar = attribute
                            case _:
                                pass

                metavar = metavar or MetaVar("value")

                option = Option(
                    parameter_name=name,
                    name=kebab_case(rename or name),
                    brief=brief,
                    target_type=target_type,
                    default_value=default_value,
                    short=short,
                    metavar=metavar,
                )
                options[name] = option
            case inspect.Parameter.VAR_KEYWORD:
                raise NotImplementedError("not implemented yet")
            case _:
                raise AssertionError(f"unreachable: {parameter.kind}")

    return (arguments, options)


class Subcommand(
    Argument,
    SupportsOptions,
    SupportsPositionalArguments,
    SupportsHelpMessage,
    Generic[T],
):
    """Represents a command-line argument that performs a task.

    This class implements the `Argument`, `SupportsOptions`,
    `SupportsPositionalArguments`, and `SupportsHelpMessage` protocols.

    Parameters
    ----------
    callback
        The function that will handle the execution of this command.
    name
        A unique identifier for the command. Defaults to `callback`'s name.
    brief
        A one-line description of what the command does. Defaults to the
        "Short Summary" section of the function's docstring.
    description
        A more detailed explanation of this command. Defaults to the
        "Extended Summary" section of the function's docstring.
    aliases
        Alternative names that can be used to invoke this command.

    Returns
    -------
    Command
        A wrapper over the callback function with additional data for exposing
        the function to the command line.

    Other Parameters
    ----------------
    positional
        A collection of `Argument` objects. By default, this is generated
        based on the function's positional arguments.
    options
        A collection of `Option` objects. By default, this is generated
        based on the function's keyword-only arguments.
    parent
        The group this command belongs to. This is typically an instance of
        `Application` or `Group`.
    """

    def __init__(
        self,
        *,
        callback: Callable[..., T],
        name: str = "",
        brief: str = "",
        description: str = "",
        aliases: MutableSequence[str] | None = None,
        positional_arguments: MutableSequence[PositionalArgument[Any]]
        | None = None,
        options: MutableMapping[str, Option[Any]] | None = None,
        parent: SupportsSubcommands | None = None,
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

        self.aliases = aliases if aliases is not None else ()

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

        self.parent = parent
        self.add_option(DEFAULT_HELP)

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
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    @property
    def positional_arguments(self) -> MutableSequence[PositionalArgument[Any]]:
        return self._positional_arguments

    @property
    def qualified_name(self) -> str:
        assert self.parent is not None, "parent should be known by now"
        assert isinstance(self.parent, SupportsHelpMessage)
        return f"{self.parent.qualified_name} {self.name}"

    def __call__(self, *args: object, **kwargs: object) -> T:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)
