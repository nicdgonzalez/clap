import inspect
from typing import Any, Callable, MutableMapping, MutableSequence

from colorize import Colorize

from .abc import Argument, SupportsOptions, SupportsSubcommands
from .docstring import parse_doc
from .errors import InvalidSignatureError
from .help import Arg, HelpFormatter, HelpMessage, Item, Section, Text, Usage
from .option import DEFAULT_HELP, Option
from .subcommand import Subcommand, parse_parameters


class Group[T](Argument, SupportsSubcommands, SupportsOptions):
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
        name: str | None = None,
        brief: str | None = None,
        description: str | None = None,
        aliases: MutableSequence[str] | None = None,
        subcommands: MutableMapping[str, "Group[Any]" | Subcommand[Any]]
        | None = None,
        options: MutableMapping[str, Option[Any]] | None = None,
        parent: SupportsSubcommands | None = None,
        invoke_without_subcommand: bool = False,
    ) -> None:
        self.callback = callback

        if name is None:
            assert hasattr(self.callback, "__name__")
            name = self.callback.__name__

        self._name = name

        parsed_doc = parse_doc(inspect.getdoc(self.callback))

        self._brief = brief or parsed_doc["short_summary"] or ""
        self.description = description or parsed_doc["extended_summary"] or ""
        self.aliases = aliases if aliases is not None else ()

        parsed_params = parse_parameters(
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

    @property
    def invoke_without_subcommand(self) -> bool:
        return self._invoke_without_subcommand

    def subcommand[U, **P](
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

    def group[U, **P](
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

    @property
    def usage(self) -> Usage:
        names = self.qualified_name.split(" ")
        assert len(names) >= 2  # Should be at least `<parent> <this_command>`
        program_name = names.pop(0)

        subcommand = str(Colorize(names.pop(0)).italic())
        names.append(subcommand)

        usage = (
            Usage(program_name)
            .add_argument(Arg(name=" ".join(names), required=None))
            .add_argument(Arg(name="options", required=False))
            .add_argument(Arg(name="--", required=False))
            .add_argument(Arg(name="command", required=True))
        )

        return usage

    def generate_help_message(self, fmt: HelpFormatter, /) -> str:
        arguments = Section("Subcommands")

        for subcommand in self.subcommands:
            arguments.add_item(
                Item(name=subcommand.name, brief=subcommand.brief)
            )

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
