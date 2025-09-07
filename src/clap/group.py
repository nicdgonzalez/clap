import inspect
from typing import (
    Any,
    Callable,
    Generic,
    MutableMapping,
    MutableSequence,
    ParamSpec,
    TypeVar,
)

from .abc import (
    Argument,
    SupportsHelpMessage,
    SupportsOptions,
    SupportsSubcommands,
)
from .docstring import parse_doc
from .errors import InvalidSignatureError
from .option import DEFAULT_HELP, Option
from .subcommand import Subcommand, _parse_parameters

T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")


class Group(
    Argument,
    SupportsSubcommands,
    SupportsOptions,
    SupportsHelpMessage,
    Generic[T],
):
    """Represents a command-line argument that groups subcommands.

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

    Other Parameters
    ----------------
    subcommands
        A collection of `Subcommand` objects.
    options
        A collection of `Option` objects. By default, this is generated
        based on the function's keyword-only arguments.
    parent
        The group this command belongs to. This is usually an instance of
        `Application` or another `Group`.

    Raises
    ------
    InvalidSignatureError
        `callback` has positional arguments.
    """

    def __init__(
        self,
        *,
        callback: Callable[..., T],
        name: str = "",
        brief: str = "",
        description: str = "",
        aliases: MutableSequence[str] | None = None,
        subcommands: MutableMapping[str, "Group[Any]" | Subcommand[Any]]
        | None = None,
        options: MutableMapping[str, Option[Any]] | None = None,
        parent: SupportsSubcommands | None = None,
        invoke_without_subcommand: bool = False,
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

        self._subcommands: MutableMapping[
            str, "Group[Any]" | Subcommand[Any]
        ] = {}

        if len(parsed_params[0]) > 0:
            raise InvalidSignatureError(
                "groups cannot have positional arguments"
            )

        self._options = options or {}

        if options is None:
            for option in parsed_params[1].values():
                self.add_option(option)

        self.parent = parent
        self._invoke_without_subcommand = invoke_without_subcommand
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
    def all_subcommands(
        self,
    ) -> MutableMapping[str, "Group[Any]" | Subcommand[Any]]:
        return self._subcommands

    @property
    def qualified_name(self) -> str:
        if self.parent is not None:
            assert hasattr(self.parent, "qualified_name")
            parent = self.parent.qualified_name

        return f"{parent} {self.name}"

    # TODO: This is not a good name for this feature.
    # Either change the way this feature works, or change the name.
    #
    # Currently, it means the group's body will always run if this is `True`.
    #
    # I don't think this is intuitive. It sounds more like this command will
    # run if the group is the last part of a CLI command.
    @property
    def invoke_without_subcommand(self) -> bool:
        return self._invoke_without_subcommand

    def subcommand(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, U]], Subcommand[U]]:
        """A convenience decorator to transform a function into a
        [`Subcommand`][clap.subcommand.Subcommand] and register it onto
        the application.

        Returns
        -------
        callable
            The inner function wrapped in a `Subcommand` object.

        See Also
        --------
        [Subcommand][clap.subcommand.Subcommand] : For valid arguments.
        """

        kwargs.setdefault("parent", self)

        def wrapper(callback: Callable[P, U]) -> Subcommand[U]:
            command = Subcommand(callback=callback, **kwargs)
            self.add_subcommand(command)
            return command

        return wrapper

    def group(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, U]], "Group[U]"]:
        """A convenience decorator to transform a function into a
        [`Group`][clap.group.Group] and register it onto
        the application.

        Returns
        -------
        callable
            The inner function wrapped in a `Group` object.

        See Also
        --------
        [Group][clap.group.Group] : For valid arguments.
        """

        kwargs.setdefault("parent", self)

        def wrapper(callback: Callable[P, U]) -> "Group[U]":
            group = Group(callback=callback, **kwargs)
            self.add_subcommand(group)
            return group

        return wrapper

    def __call__(self, *args: object, **kwargs: object) -> T:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)
