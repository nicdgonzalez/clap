from __future__ import annotations

from builtins import list as List
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from .utils import MISSING

if TYPE_CHECKING:
    from builtins import type as Type
    from typing import Optional

    T = TypeVar("T")


def is_generic_type(cls: Type[Any], /) -> bool:
    return (
        isinstance(cls, type) and issubclass(cls, Generic[Any])
    ) or isinstance(cls, type(List[Any]))


def convert_to_bool(argument: str, /) -> bool:
    if argument.lower() in ("yes", "y", "true", "t", "1"):
        return True
    elif argument.lower() in ("no", "n", "false", "f", "0"):
        return False
    else:
        raise ValueError("unable to convert {!r} to bool".format(argument))


def actual_conversion(argument: str, converter: Type[Any]) -> Optional[Any]:
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
    converter: Type[Any],
    /,
    default: T = MISSING,
) -> Optional[Any]:
    # TODO: finish converter logic
    origin = get_origin(converter)

    if origin is Union:
        # union_args = get_args(converter)
        raise NotImplementedError
    elif origin is Literal:
        raise NotImplementedError
    elif origin is not None and is_generic_type(converter):
        converter = origin

    return actual_conversion(argument, converter)
