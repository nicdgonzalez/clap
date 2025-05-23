import types
import typing
from typing import Any, Callable, get_args, get_origin

from .errors import ArgumentError
from .sentinel import MISSING


def is_generic_type(tp: Callable[[str], Any], /) -> bool:
    return (
        isinstance(tp, type) and issubclass(tp, typing.Generic)  # type: ignore[arg-type]  # noqa: E501
    ) or isinstance(tp, type(list[int]))


def convert[T](
    *,
    argument: str,
    converter: Callable[[str], T],
    default_value: T = MISSING,
) -> T:
    origin = get_origin(tp=converter)

    match origin:
        case types.UnionType | typing.Union:
            args = get_args(converter)
            errors: list[str] = []

            for arg in args:
                if arg is None:
                    # At this point, we know `None` is a valid `T`.
                    return None if default_value is MISSING else default_value  # type: ignore[return-value]  # noqa: E501

                try:
                    value = convert(
                        argument=argument,
                        converter=arg,
                        default_value=default_value,
                    )
                except Exception as exc:
                    errors.append(str(exc))
                else:
                    return value

            args_tried = ", ".join(
                [
                    arg.__name__
                    if hasattr(arg, "__name__")
                    else arg.__class__.__name__
                    for arg in args
                ]
            )
            raise ArgumentError(
                f"unable to convert {argument!r} into one of ({args_tried})"
            )
        case typing.Literal:
            args = get_args(converter)

            for arg in args:
                t = type(arg)

                try:
                    value = convert(
                        argument=argument,
                        converter=t,
                        default_value=default_value,
                    )
                except Exception:
                    continue

                if value == arg:
                    return value
                else:
                    pass
            else:
                raise ArgumentError(
                    f"expected {argument!r} to be one of: [{', '.join(args)}]"
                )
        case _:
            if origin is not None and is_generic_type(converter):
                converter = origin  # type: ignore[assignment]

            if converter is bool:
                match argument.lower():
                    case "yes" | "y" | "true" | "t" | "1":
                        # At this point, we know `True` is a valid `T`.
                        return True  # type: ignore[return-value]
                    case "no" | "n" | "false" | "f" | "0":
                        # At this point, we know `False` is a valid `T`.
                        return False  # type: ignore[return-value]
                    case _:
                        raise ArgumentError(
                            f"unable to convert {argument!r} to 'bool'"
                        )

            try:
                return converter(argument)
            except Exception:
                try:
                    name = converter.__name__
                except AttributeError:
                    name = converter.__class__.__name__

                raise ArgumentError(
                    f"unable to convert {argument!r} to {name!r}"
                )

    return converter(argument)
