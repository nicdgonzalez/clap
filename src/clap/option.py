from .convert import convert
from .metadata import Short
from .sentinel import MISSING


class Option[T]:
    def __init__(
        self,
        name: str,
        cls: type[T],
        short: Short | None = None,
        default: T | MISSING = MISSING,
        help: str | None = None,
    ) -> None:
        self.name = name
        self.cls = cls
        self.short = short
        self.default = default
        self.help = help

    def convert(self, argument: str) -> T:
        return convert(argument, self.cls, self.default)
