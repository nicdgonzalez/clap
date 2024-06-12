from __future__ import annotations

from typing import TYPE_CHECKING

from .abc import ParameterizedArgument

if TYPE_CHECKING:
    from typing import Optional


class Option(ParameterizedArgument):

    def __init__(
        self, name: str, brief: str, *, alias: Optional[str] = None
    ) -> None:
        self._name = name
        self._brief = brief

        if alias is not None and len(alias) > 1:
            raise ValueError("option alias must be a single character or None")

        self._alias = alias

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def alias(self) -> Optional[str]:
        return self._alias
