from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable

# fmt: off
__all__ = (
    "Command",
)
# fmt: on


class Command:

    def __init__(self, callback: Callable[..., Any], /) -> None:
        if not callable(callback):
            raise TypeError("callback must be a callable object")

        self.callback = callback

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.callback(*args, **kwargs)
