import abc

__all__ = (
    "Action",
    "Count",
)


class Action(abc.ABC):
    pass


class Store(Action):
    """Save the value of the command-line option as-is."""


class Count(Action):
    """Count the number of times an option has occurred."""
