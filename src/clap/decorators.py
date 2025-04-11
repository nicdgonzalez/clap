from typing import Any, Callable

from .group import Group
from .script import Script
from .subcommand import Subcommand


def subcommand[T, **P](
    *args: Any, **kwargs: Any
) -> Callable[[Callable[P, T]], Subcommand[T]]:
    """A decorator to convert a method into a
    [`Subcommand`][clap.subcommand.Subcommand].

    Returns
    -------
    callable
        The inner function wrapped in a `Subcommand` object.

    See Also
    --------
    [Subcommand][clap.subcommand.Subcommand] : For valid arguments.
    """

    def wrapper(callback: Callable[P, T]) -> Subcommand[T]:
        return Subcommand(callback=callback, *args, **kwargs)

    return wrapper


def group[T, **P](
    *args: Any, **kwargs: Any
) -> Callable[[Callable[P, T]], Group[T]]:
    """A decorator to convert a method into a [`Group`][clap.group.Group].

    Returns
    -------
    callable
        The inner function wrapped in a `Group` object.

    See Also
    --------
    [Group][clap.group.Group] : For valid arguments.
    """

    def wrapper(callback: Callable[P, T]) -> Group[T]:
        return Group(callback=callback, *args, **kwargs)

    return wrapper


def script[T, **P](
    *args: Any, **kwargs: Any
) -> Callable[[Callable[P, T]], Script[T]]:
    """A decorator to convert a function into a [`Script`][clap.script.Script].

    Returns
    -------
    callable
        The inner function wrapped in a `Script` object.

    See Also
    --------
    [Script][clap.script.Script] : For valid arguments.
    """

    def wrapper(callback: Callable[P, T]) -> Script[T]:
        return Script(callback=callback, *args, **kwargs)

    return wrapper
