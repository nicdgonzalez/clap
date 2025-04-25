from __future__ import annotations

from typing import TYPE_CHECKING, Any, MutableMapping

from .abc import SupportsSubcommands
from .group import Group
from .subcommand import Subcommand

if TYPE_CHECKING:
    from .application import Application


def add_member_subcommands(parent: SupportsSubcommands, /) -> None:
    members = tuple(parent.__class__.__dict__.values())

    for subcommand in members:
        if not isinstance(subcommand, (Group, Subcommand)):
            continue

        subcommand.parent = parent

        # Decorators on class methods wrap around an unbound method;
        # we need to set the `__self__` attribute manually.
        if not hasattr(subcommand.callback, "__self__"):
            setattr(subcommand.callback, "__self__", parent)

        parent.add_subcommand(subcommand)


class Extension(SupportsSubcommands):
    if TYPE_CHECKING:
        _subcommands: MutableMapping[str, Group[Any] | Subcommand[Any]]

    def __new__(cls, *args: Any, **kwargs: Any) -> "Extension":
        this = super().__new__(cls)
        this._subcommands = {}
        add_member_subcommands(this)
        return this

    def __init__(self, app: Application, /, *args: Any, **kwargs: Any) -> None:
        self.app = app
