from typing import Callable, Iterable, Mapping

from .argument import Argument
from .option import Option


class Command:
    """Represents a command-line argument that performs an action"""

    def __init__(
        self,
        callback: Callable[..., None],
        name: str = "",
        brief: str = "",
        description: str = "",
        aliases: Iterable[str] | None = None,
        arguments: Iterable[Argument] | None = None,
        options: Mapping[str, Option] | None = None,
    ) -> None:
        self.callback = callback

        if name == "":
            assert hasattr(self.callback, "__name__")
            name = self.callback.__name__

        self.name = name

        if brief == "":
            # Get brief from first line of the function's docstring.
            ...

        self.brief = brief

        if description == "":
            # Get description from the next paragraph of the function's docstring.
            ...

        self.description = description

        self.aliases = aliases if aliases is not None else []

        if arguments is None:
            # Get arguments from the function's type annotations.
            ...

        self.arguments = arguments

        if options is None:
            # Get the options from the function's type annotations.
            ...

        self.options = options

    def __call__(self, *args: object, **kwargs: object) -> None:
        # TODO: Handle case where callback is a class method.
        _ = self.callback(*args, **kwargs)
