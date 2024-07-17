from __future__ import annotations

import types
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from .utils import MISSING

if TYPE_CHECKING:
    from typing import Optional

    T = TypeVar("T")

# TODO: Allow users to create custom converters.


def is_generic_type(cls: type[Any], /) -> bool:
    return (
        isinstance(cls, type)
        and issubclass(cls, Generic)  # type: ignore  # Works fine at runtime
        or isinstance(cls, type(list[Any]))
    )


def convert_to_bool(argument: str, /) -> bool:
    if argument.lower() in ("yes", "y", "true", "t", "1"):
        return True
    elif argument.lower() in ("no", "n", "false", "f", "0"):
        return False
    else:
        raise ValueError("unable to convert {!r} to bool".format(argument))


def actual_conversion(argument: str, converter: type[Any]) -> Optional[Any]:
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
    converter: type[Any],
    /,
    default: T = MISSING,
) -> Optional[Any]:
    origin = get_origin(converter)

    if origin in (types.UnionType, Union):
        errors: list[Exception] = []
        union_args = get_args(converter)

        for arg in union_args:
            if arg is None:
                return None if default is MISSING else default

            try:
                value = convert(argument, arg, default)
            except Exception as exc:
                errors.append(exc)
            else:
                return value

        raise ValueError(
            "unable to convert {!r} to one of {!r}: {}".format(
                argument, union_args, errors
            )
        )
    elif origin is Literal:
        valid_literals = get_args(converter)

        for literal in valid_literals:
            literal_type = type(literal)

            try:
                value = convert(argument, literal_type, default)
            except Exception:
                continue

            if value == literal:
                return value

    elif origin is not None and is_generic_type(converter):
        converter = origin

    return actual_conversion(argument, converter)
