from typing import Any

__all__ = ("MISSING",)


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


# Since `None` can be a valid value in certain contexts, we can use `MISSING`
# to explicitly indicate the absence of a value.
MISSING: Any = _Missing()
