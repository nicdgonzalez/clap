import importlib
import os
import sys
import textwrap
from typing import (
    Any,
    Callable,
    Generic,
    MutableMapping,
    ParamSpec,
    Sequence,
    TypeVar,
)

from .abc import (
    Argument,
    SupportsHelpMessage,
    SupportsOptions,
    SupportsSubcommands,
)
from .errors import MissingSetupFunctionError
from .extension import Extension, add_member_subcommands
from .group import Group
from .help import HelpFormatter, HelpMessage, Text
from .option import DEFAULT_HELP, Option
from .parser import parse
from .subcommand import Subcommand

T = TypeVar("T")
P = ParamSpec("P")


class Application(
    Argument,
    SupportsOptions,
    SupportsSubcommands,
    SupportsHelpMessage,
    Generic[T],
):
    """Represents the project itself.

    You can think of it like this object represents `sys.argv[0]`. This is the
    base command of a project that uses multiple subcommands to perform tasks.

    This class implements the `Argument`, `SupportsOptions`,
    `SupportsSubcommands`, and `SupportsHelpMessage` protocols.

    Parameters
    ----------
    name
        The program name. Defaults to the basename of `sys.argv[0]`.
    brief
        A one-line summary of this application.
    description
        A paragraph explaining the application in more detail.
    after_help
        Add an arbitrary message to the end of the help text.
    """

    def __init__(
        self,
        *,
        name: str = os.path.basename(sys.argv[0]),
        brief: str = "",
        description: str = "",
        after_help: str = "",
    ) -> None:
        self._name = name.strip()
        self._brief = brief.strip()
        self._description = textwrap.dedent(description).strip()
        self.after_help = after_help.strip()

        self._subcommands: dict[str, Group[Any] | Subcommand[Any]] = {}
        self._options: dict[str, Option[Any]] = {}
        self.add_option(DEFAULT_HELP)
        add_member_subcommands(self)

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
    def all_subcommands(
        self,
    ) -> MutableMapping[str, Group[Any] | Subcommand[Any]]:
        return self._subcommands

    @property
    def all_options(self) -> MutableMapping[str, Option[Any]]:
        return self._options

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        help_message = self.get_help_message()
        print(help_message.render(HelpFormatter()))

    def extend(self, name: str, package: str | None = None) -> None:
        """Load subcommands from an [`Extension`][clap.extension.Extension]
        onto the main application.

        Parameters
        ----------
        name
            The name of the module to import in dot format (the same format
            used when importing modules; e.g., `clap.errors`)
        package
            Required when using relative module names (e.g., `clap.errors` can
            also be imported as `name=".errors"` and `package="clap"`).

        Raises
        ------
        ImportError
            The target module was not found.
        clap.errors.MissingSetupFunctionError
            The target module exists, but the global `setup` function was
            not defined. See documentation for more information.
        """
        module = importlib.import_module(name, package=package)
        setup_fn = getattr(module, "setup", None)

        if setup_fn is None:
            raise MissingSetupFunctionError(module=module)

        _ = setup_fn(self)

    def add_extension(self, extension: Extension, /) -> None:
        for subcommand in extension.subcommands:
            self.add_subcommand(subcommand)

    def subcommand(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, T]], Subcommand[T]]:
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

        def wrapper(callback: Callable[P, T]) -> Subcommand[T]:
            command = Subcommand(callback=callback, **kwargs)
            self.add_subcommand(command)
            return command

        return wrapper

    def group(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[P, T]], Group[T]]:
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

        def wrapper(callback: Callable[P, T]) -> Group[T]:
            group = Group(callback=callback, **kwargs)
            self.add_subcommand(group)
            return group

        return wrapper

    def get_help_message(self) -> HelpMessage:
        help_message = SupportsHelpMessage.get_help_message(self)
        return help_message.add(Text(self.after_help))

    def parse_args(
        self,
        input: Sequence[str] = sys.argv[slice(1, None, 1)],
        *,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> Any:
        return parse(self, input=input, formatter=formatter)
