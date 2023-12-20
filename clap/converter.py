"""
Converter
=========

This module implements the :func:`convert` function, which is used to convert
command-line arguments to Python objects.

"""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    List,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import type as Type
    from typing import Optional

__all__ = ["convert"]

T = TypeVar("T")
_GenericAlias = type(List[Any])


# Adapted from: https://github.com/rapptz/discord.py


def is_generic_type(cls: Any, _GenericAlias: Type = _GenericAlias) -> bool:
    """Check if a type is a generic type.

    Parameters
    ----------
    cls : :class:`type`
        The type to check.

    Returns
    -------
    :class:`bool`
        Whether the type is a generic type.
    """
    return (
        isinstance(cls, type)
        and issubclass(cls, Generic[Any])
        or isinstance(cls, _GenericAlias)
    )


def convert_to_bool(argument: str, /) -> bool:
    """Convert a string to a boolean value.

    Parameters
    ----------
    argument : :class:`str`
        The string to convert.

    Returns
    -------
    :class:`bool`
        The converted boolean value.

    Raises
    ------
    :exc:`ValueError`
        If the string could not be converted to a boolean value.
    """
    if argument.lower() in ("yes", "y", "true", "t", "1"):
        return True
    elif argument.lower() in ("no", "n", "false", "f", "0"):
        return False
    else:
        raise ValueError(f"Unable to convert {argument!r} to bool")


def actual_conversion(
    converter: Type[T],
    argument: str,
) -> T:
    """Convert a command-line argument to a Python object.

    Parameters
    ----------
    converter : :class:`type`
        The type to which the argument's value will be converted.
    argument : :class:`str`
        The command-line argument to convert.

    Returns
    -------
    :class:`T`
        The converted command-line argument.

    Raises
    ------
    :exc:`ValueError`
        If the argument could not be converted to the target type.
    """
    if converter is bool:
        return cast(T, convert_to_bool(argument))

    try:
        return converter(argument)
    except Exception as exc:
        try:
            name = converter.__name__
        except AttributeError:
            name = converter.__class__.__name__

        raise ValueError(
            f"Unable to convert {argument!r} to {name!r}"
        ) from exc


def convert(
    converter: Type[T],
    argument: str,
    default: T = MISSING,
) -> Optional[T]:
    """Serialize a command-line argument to a Python object.

    Parameters
    ----------
    converter : :class:`type`
        The type to which the argument's value will be converted.
    argument : :class:`str`
        The command-line argument to convert.
    default : :class:`T`
        The default value of the argument.

    Returns
    -------
    :class:`T`
        The converted command-line argument.

    Raises
    ------
    :exc:`ValueError`
        If the argument could not be converted to the target type.
    """
    origin = get_origin(converter)
    value: Optional[T]

    if origin is Union:
        errors: List[Exception] = []
        _NoneType = type(None)
        union_args = get_args(converter)

        for arg in union_args:
            # NoneType is the last argument in a Union, so if we've reached
            # it, we've exhausted all other options.
            if arg is _NoneType:
                return None if default is not MISSING else default

            try:
                value = convert(arg, argument, default)
            except Exception as exc:
                errors.append(exc)
            else:
                return value

        raise ValueError(
            f"Unable to convert {argument!r} to one of {union_args!r}"
        )

    if origin is Literal:
        conversions: Dict[Type[Any], Any] = {}
        valid_literals = get_args(converter)

        for literal in valid_literals:
            literal_type = type(literal)

            try:
                value = convert(literal_type, argument, default)
            except KeyError:
                try:
                    value = actual_conversion(literal_type, argument)
                except Exception:
                    conversions[literal_type] = object()
                    continue
                else:
                    conversions[literal_type] = value

            if value == literal:
                return value

        raise ValueError(
            f"Unable to convert {argument!r} to one of {valid_literals!r}"
        )

    if origin is not None and is_generic_type(converter):
        converter = origin

    return actual_conversion(converter, argument)
