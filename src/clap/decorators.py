from typing import Callable, Iterable

from .command import Command


def command(
    *,
    name: str = "",
    aliases: Iterable[str] = (),
) -> Callable[[Callable[..., None]], Command]:
    """A convenience decorator to convert a function into a `.command.Command`.

    Parameters
    ----------
    name: :class:`str`
        An alternative identifier to use for the subcommand.
    """

    def wrapper(callback: Callable[..., None]) -> Command:
        return Command(callback=callback)

    return wrapper
