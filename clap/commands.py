from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from .abc import HasCommands, HasOptions, HasPositionalArgs
from .arguments import Positional
from .utils import parse_docstring

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Callable, Optional

    from typing_extensions import Self

    from .options import Option

__all__ = ("Command",)


class Command(HasOptions, HasPositionalArgs):

    def __init__(
        self,
        callback: Callable[..., Any],
        /,
        name: str,
        brief: str,
        description: str,
        aliases: List[str],
        options: Dict[str, Option],
        positionals: List[Positional],
        parent: Optional[HasCommands],
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")

        self._callback = callback
        self._name = name
        self._brief = brief
        self._description = description
        self._aliases = aliases
        self._options = options
        self._positionals = positionals
        self._parent = parent

    @classmethod
    def from_function(
        cls,
        callback: Callable[..., Any],
        /,
        **kwargs: Any,
    ) -> Self:
        if not callable(callback):
            raise TypeError("callback must be callable")

        kwargs.setdefault("name", callback.__name__)
        parsed_docstring = parse_docstring(inspect.getdoc(callback) or "")
        kwargs.setdefault("brief", parsed_docstring.get("__brief__", ""))
        kwargs.setdefault("description", parsed_docstring.get("__desc__", ""))
        kwargs.setdefault("aliases", [])
        kwargs.setdefault("options", {})
        kwargs.setdefault("positionals", [])
        kwargs.setdefault("parent", None)
        return cls(callback, **kwargs)

    @property
    def all_options(self) -> Dict[str, Option]:
        return self._options

    @property
    def all_positionals(self) -> List[Positional]:
        return self._positionals

    @property
    def callback(self) -> Callable[..., Any]:
        return self._callback

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def description(self) -> str:
        return self._description

    @property
    def aliases(self) -> List[str]:
        return self._aliases

    @property
    def parent(self) -> Optional[HasCommands]:
        return self._parent

    @parent.setter
    def parent(self, value: HasCommands) -> None:
        if not isinstance(value, HasCommands):
            raise TypeError("value does not satisfy the HasCommands protocol")

        self._parent = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if hasattr(self.callback, "__self__"):
            return self.callback(self.callback.__self__, *args, **kwargs)
        else:
            return self.callback(*args, **kwargs)
