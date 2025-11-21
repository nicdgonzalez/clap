import enum


class Action(enum.IntEnum):
    """Indicates how to interpret the command-line arguments."""

    STORE = enum.auto()
    COUNT = enum.auto()


class Metadata:
    __slots__ = ()


class Long(Metadata):
    """Indicate this argument is an option with a long flag.

    The value defaults to the class member name.

    Examples
    --------
    >>> from clap import Long
    >>> from typing import Annotated
    >>>
    >>> class Parser(clap.ArgumentParser):
    ...     verbose: Annotated[int, Action.COUNT, Long()]
    >>>
    >>> args = Parser.try_parse(args=["--verbose"])
    >>> assert args.verbose == 1
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass


class Short(Metadata):
    """Indicates this argument is an option with a short flag.

    Parameters
    ----------
    value
        Single character (e.g., `"h"` for `-h`, `"f"` for `-f`).
        Defaults to the first letter of the class member name.
    """

    __slots__ = ("value",)

    def __init__(self, value: str | None = None) -> None:
        if value is not None and len(value) != 1:
            raise ValueError("value must be a single character")

        self.value = value


class Help(Metadata):
    """A brief message about the argument.

    Parameters
    ----------
    value
        One-line explanation of the argument
    """

    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value
