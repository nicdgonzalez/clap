from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar, Union, get_args, get_origin

from .utils import MISSING

if TYPE_CHECKING:
    from builtins import type as Type
    from typing import Any, Optional

    T = TypeVar("T")


def is_generic_type(cls: Type[Any], /) -> bool:
    raise NotImplementedError


def convert_to_bool(argument: str, /) -> bool:
    if argument.lower() in ("yes", "y", "true", "t", "1"):
        return True
    elif argument.lower() in ("no", "n", "false", "f", "0"):
        return False
    else:
        raise ValueError("unable to convert {!r} to bool".format(argument))


def actual_conversion(argument: str, converter: Type[T]) -> Optional[T]:
    if converter is bool:
        return convert_to_bool(argument)

    try:
        return converter(argument)
    except Exception as exc:
        try:
            name = converter.__name__
        except AttributeError:
            name = converter.__class__.__name__

        raise ValueError(
            "unable to convert {!r} to {!r}".format(argument, name)
        ) from exc


def convert(
    argument: str,
    converter: Type[T],
    /,
    default: T = MISSING,
) -> Optional[T]:
    origin = get_origin(converter)
    # value: Optional[T]

    if origin is Union:
        union_args = get_args(converter)
        print(union_args)
        raise NotImplementedError
    elif origin is Literal:
        raise NotImplementedError
    elif origin is not None and is_generic_type(converter):
        converter = origin

    return actual_conversion(argument, converter)
