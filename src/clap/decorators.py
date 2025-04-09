from typing import Any, Callable

from .command import Command


def command[T, **P](
    *args: Any, **kwargs: Any
) -> Callable[[Callable[P, T]], Command[T]]:
    """A decorator to convert a method into a
    [`Command`][clap.command.Command].

    Returns
    -------
    callable
        The inner function wrapped in a `Command` object.

    See Also
    --------
    [Command][clap.command.Command] : For valid arguments to this function.
    """

    def wrapper(callback: Callable[P, T]) -> Command[T]:
        return Command(callback=callback)

    return wrapper
