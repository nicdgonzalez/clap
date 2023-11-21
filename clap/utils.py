"""
Utils
=====

This module contains utility functions and classes used by the other modules.

"""
from __future__ import annotations

import re
from typing import Any


class _Missing:
    __slots__ = ()

    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _Missing()


def fold_text(text: str, /) -> str:
    """Remove unnecessary whitespaces and replace tabs and newlines with
    a single space.

    Parameters
    ----------
    text : str
        The text to clean.

    Returns
    -------
    str
        The cleaned text.
    """
    return re.sub(r"\s+", " ", text).strip()
