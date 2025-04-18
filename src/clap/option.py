import pathlib

from .abc import SupportsConvert
from .attributes import MetaVar, Short
from .sentinel import MISSING


class Option[T](SupportsConvert[T]):
    """Represents a command-line flag (e.g., `--verbose`)"""

    def __init__(
        self,
        *,
        name: str,
        brief: str,
        target_type: type,
        default_value: T = MISSING,
        short: Short | None = None,
        metavar: MetaVar | None = None,
    ) -> None:
        self._name = name
        self._brief = brief
        self._target_type = target_type
        self._default_value = default_value
        self.short = short
        self.metavar = metavar or "value"

    @property
    def name(self) -> str:
        return self._name

    @property
    def brief(self) -> str:
        if self._target_type is bool or self._default_value is MISSING:
            return self._brief

        match self._default_value:
            case pathlib.Path():
                default = self._default_value.as_posix().replace(
                    pathlib.Path.cwd().as_posix(), "."
                )
            case _:
                default = self._default_value

        return self._brief + f" [{default}]"

    @property
    def target_type(self) -> type:
        return self._target_type

    @property
    def default_value(self) -> T:
        return self._default_value


DEFAULT_HELP = Option(
    name="help",
    brief="Display this help message and exit",
    target_type=bool,
    default_value=False,
    short=Short("h"),
)
