"""
Metadata
========

This module contains the types that can be used in conjunction with
:class:`typing.Annotated` to provide additional information about the
type that would otherwise not be expressible.

Examples
--------
>>> from typing import Annotated
>>>
>>> import clap
>>>
>>>
>>> @clap.command()
>>> def create_user(name: Annotated[str, clap.Range(3, 20)], /) -> None:
...     \"\"\"Add a new user to the database.
...
...     Parameters
...     ----------
...     name : str
...         The name of the user. Must be between 3 and 20 characters long.
...     \"\"\"
...     pass

For example, it would not be possible to express that the ``name`` parameter
must be between 3 and 20 characters long using only the :class:`str` type.
However, by using :class:`typing.Annotated` and :class:`.Range`, this
information can be expressed and used by the command-line parser.

"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import tuple as Tuple
    from typing import Any, Optional


class Short(str):
    """Represents a single-character alias for a :class:`.Option`.

    This type is not meant to be used directly. Instead, pass it as an
    additional argument to :class:`typing.Annotated` when annotating function
    parameters.

    Parameters
    ----------
    value : str
        The alias to use for the option. Must be a single character.

    Raises
    ------
    :exc:`ValueError`
        If the alias is not a single character.
    """

    def __new__(cls, value: str) -> Short:
        if len(value) != 1:
            raise ValueError("option alias must be a single character")

        return super().__new__(cls, value)


class Range(NamedTuple):
    """Represents a range of values that a :class:`.Option` can take.

    This type is not meant to be used directly. Instead, pass it as an
    additional argument to :class:`typing.Annotated` when annotating function
    parameters.

    For example,

    - Annotated[int, Range(0, 10)]: Accepts 0 to 10 integers of any value.
    - Annotated[int, Range(3, None)]: Accept 3 or more integers of any value.

    Parameters
    ----------
    minimum : int
        The minimum value that the option can take. This value must be
        greater than or equal to 0.
    maximum : Optional[:class:`int`]
        The maximum value that the option can take. If ``None``, there is no
        maximum value.
    """

    minimum: int
    maximum: Optional[int]


if sys.version_info >= (3, 9):
    _Set = set[str]
else:
    _Set = set


class Requires(_Set):
    """A set of options that are required by an :class:`.Option`.

    This type is not meant to be used directly. Instead, pass it as an
    additional argument to :class:`typing.Annotated` when annotating function
    parameters.
    """

    def __init__(self, *options: str) -> None:
        super().__init__(options)


class Conflicts(_Set):
    """A set of options names that are mutually exclusive with an
    :class:`.Option`.

    This type is not meant to be used directly. Instead, pass it as an
    additional argument to :class:`typing.Annotated` when annotating function
    parameters.
    """

    def __init__(self, *options: str) -> None:
        super().__init__(options)


def extract_metadata(metadata: Tuple[Any, ...], /) -> Dict[str, Any]:
    """Convert the values from the ``__metadata__`` attribute into a
    dictionary.

    Parameters
    ----------
    metadata : :class:`tuple`
        The metadata to convert. This is the ``__metadata__`` attribute of
        a type like ``typing.Annotated``.

    Returns
    -------
    :class:`dict`
        A dictionary mapping the metadata to valid keyword arguments for
        :class:`Argument` or :class:`Option`.
    """
    data: Dict[str, Any] = {}

    mapping = {
        # Both `Argument` and `Option` accepts these.
        Range: "n_args",
        # Only `Option` accepts these.
        Short: "alias",
        Requires: "requires",
        Conflicts: "conflicts",
    }

    for value in metadata:
        if isinstance(value, Range):
            data["n_args"] = (value.minimum, value.maximum)
            continue

        try:
            key = mapping[type(value)]
        except KeyError:
            continue  # Ignore any unknown metadata.

        data[key] = value

    return data
