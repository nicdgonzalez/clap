from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Generic, TypeVar

from .abc import CallableArgument, SupportsCommands, SupportsOptions
from .option import Option
from .positional import Positional
from .utils import MISSING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Callable, Optional, Self, Union

    from .abc import PositionalArgument

# fmt: off
__all__ = (
    "Command",
    "Group",
)
# fmt: on

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")

DEFAULT_HELP = Option(
    name="help",
    brief="Display this help message and exit.",
    target_type=bool,
    default=False,
    n_args=0,
    alias="h",
)

if TYPE_CHECKING:
    _ParameterKind = type(inspect.Parameter.kind)

parameter_kind_map: Dict[_ParameterKind, PositionalArgument[Any]] = {
    inspect.Parameter.POSITIONAL_ONLY: Positional,
    inspect.Parameter.VAR_POSITIONAL: Positional,
    inspect.Parameter.POSITIONAL_OR_KEYWORD: Positional,
    inspect.Parameter.KEYWORD_ONLY: Option,
    inspect.Parameter.VAR_KEYWORD: Option,
}


class CommandBase(SupportsOptions, Generic[T_co]):
    def __init__(
        self,
        *,
        callback: Optional[Callable[..., T_co]],
        name: str,
        brief: str,
        description: str,
        aliases: Union[List[str], None],
        parent: Optional[SupportsCommands],
    ) -> None:
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable")

        self._callback = callback
        self._name = name
        self._brief = brief
        self._description = description
        self._aliases = aliases
        self.all_options = {}
        self.add_option(DEFAULT_HELP)

        if parent is not None and not isinstance(parent, SupportsCommands):
            raise TypeError(
                "parent must implement the `SupportsCommands` protocol"
            )

        self.parent = parent

    @classmethod
    def from_callback(
        cls,
        callback: Callable[..., T_co],
        /,
        aliases: Union[List[str], None],
        parent: Optional[SupportsCommands],
        **kwargs: Any,
    ) -> Self:
        descriptions = parse_docstring(inspect.getdoc(callback) or "")

        kwargs.setdefault("name", callback.__name__)
        kwargs.setdefault("brief", descriptions.get("__brief__", ""))
        kwargs.setdefault("description", descriptions.get("__desc__", ""))
        self = cls(callback=callback, **kwargs)

        parameters = inspect.signature(callback).parameters
        parameter_values = list(parameters.values())

        has_removable_self = hasattr(callback, "__self__") or (
            # Likely an unbound method, though this is just an educated guess.
            inspect.isfunction(callback)
            and "." in callback.__qualname__
            and parameters.get("self", None) is not None
        )

        if has_removable_self:
            _ = parameter_values.pop(0)

        parameter_types = inspect.get_annotations(callback, eval_str=True)

        for parameter in parameter_values:
            argument_cls = parameter_kind_map[parameter.kind]
            argument = argument_cls.from_parameter(
                parameter,
                brief=descriptions[parameter.name],
                target_type=parameter_types[parameter.name],
                default_value=(
                    parameter.default
                    if parameter.default is not parameter.empty
                    else MISSING
                ),
                n_args=-1,  # TODO: Try to extract this from metadata.
            )

            if isinstance(argument, Option):
                self.add_option(argument)
            elif isinstance(argument, Positional):
                self.add_positional(argument)
            else:
                raise NotImplementedError

        return self

    def add_argument(self, argument: Positional[Any], /) -> None:
        if isinstance(argument, Option):
            self.add_option(argument)
        elif isinstance(argument, Positional):
            # Option derives from Positional, so be sure it comes after.
            self.add_positional(argument)
        else:
            raise TypeError(
                f"Failed to add Argument {argument.name!r}. "
                "Argument type is not supported"
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        return self._brief

    @property
    def callback(self) -> Optional[Callable[..., T_co]]:
        return self._callback

    @staticmethod
    def _handle_parameters() -> None:
        return None


class Command(CommandBase[T_co]):
    def __init__(
        self,
        callback: Callable[..., T_co],
        *args: Any,
        name: str,
        brief: str,
        description: str,
        aliases: List[str],
        parent: Optional[SupportsCommands] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            callback=callback,
            name=name,
            brief=brief,
            description=description,
            aliases=aliases or [],
            parent=parent,
        )


class Group(CommandBase[None], SupportsCommands):
    def __new__(cls) -> Self:
        this = super().__new__(cls)
        this.all_commands = {}

        # `inspect.getmembers` sorts the attributes alphabetically;
        # `__dict__` is used instead to retain the original order.
        for cmd in this.__class__.__dict__.values():
            if not isinstance(cmd, CallableArgument):
                continue

            if isinstance(this, SupportsCommands):
                cmd.parent = this

            # Decorators on class methods wrap around the unbound method;
            # we need to set the `__self__` attribute manually.
            if not hasattr(cmd.callback, "__self__"):
                setattr(cmd.callback, "__self__", this)

            this.add_command(cmd)

        return this

    def __init__(
        self,
        callback: Callable[..., None],
        *args: Any,
        name: str,
        brief: str,
        description: str,
        aliases: List[str],
        parent: Optional[SupportsCommands] = None,
        invoke_without_command: bool = False,
    ) -> None:
        super().__init__(
            callback=callback,
            name=name,
            brief=brief,
            description=description,
            aliases=aliases or [],
            parent=parent,
        )

        self.invoke_without_command = invoke_without_command

    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[..., Command[Any]]:
        def decorator(callback: Callable[..., Any], /) -> Command[Any]:
            kwargs.setdefault("parent", self)
            c = Command(callback=callback, *args, **kwargs)
            self.add_command(c)
            return c

        return decorator

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., Group]:
        def decorator(callback: Callable[..., Any], /) -> Group:
            kwargs.setdefault("parent", self)
            kwargs.setdefault("aliases", [])
            g = Group(callback=callback, *args, **kwargs)
            self.add_command(g)
            return g

        return decorator


def parse_docstring(docstring: str, /) -> Dict[str, str]:
    return {}
