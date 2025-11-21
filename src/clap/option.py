from .convert import convert
from .metadata import Short
from .sentinel import MISSING


class Option[T]:
    def __init__(
        self,
        name: str,
        tp: type[T],
        short: Short | None = None,
        default: T | MISSING = MISSING,
        help: str | None = None,
    ) -> None:
        self.name = name
        self.tp = tp
        self.short = short
        self.default = default
        self.help = help

    def convert(self, argument: str) -> T:
        return convert(argument, self.tp, self.default)
