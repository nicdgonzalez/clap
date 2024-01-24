from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from .metadata import Conflicts, Range, Requires, Short
from .positional import Positional
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import type as Type
    from typing import Any, Optional, Union

# fmt: off
__all__ = (
    "Option",
)
# fmt: on

T = TypeVar("T")


class Option(Positional[T]):
    def __init__(
        self,
        *,
        name: str,
        brief: str,
        target_type: Type[T],
        default_value: T = MISSING,
        n_args: Union[Range, int] = Range(0, 1),
        alias: Optional[Union[Short, str]] = None,
        requires: Requires = MISSING,
        conflicts: Conflicts = MISSING,
    ) -> None:
        super().__init__(
            name=name,
            brief=brief,
            target_type=target_type,
            default_value=default_value,
            n_args=n_args,
        )

        if alias is not None and not isinstance(alias, Short):
            alias = Short(alias)

        self.alias = alias
        self.requires = requires or Requires()
        self.conflicts = conflicts or Conflicts()

    @property
    def snake_case(self) -> str:
        return self.name.replace("-", "_")

    @property
    def kebab_case(self) -> str:
        return self.name.replace("_", "-")
