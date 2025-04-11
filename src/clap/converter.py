import types
import typing
from typing import Callable, get_args, get_origin

from .sentinel import MISSING


def convert[T](
    *,
    argument: str,
    converter: Callable[[str], T],
    default_value: T = MISSING,
) -> T:
    # TODO: Handle cases where T is a Generic, Literal, Union, etc.
    match get_origin(converter):
        case types.UnionType | typing.Union:
            args = get_args(converter)

            for arg in args:
                if arg is None:
                    # A
                    ...

    return converter(argument)
