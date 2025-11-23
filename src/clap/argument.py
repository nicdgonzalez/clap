from .convert import convert
from .sentinel import MISSING


class Argument[T]:
    def __init__(
        self,
        name: str,
        cls: type[T],
        default: T | MISSING = MISSING,
        help: str | None = None,
    ) -> None:
        self.name = name
        self.cls = cls
        self.default = default
        self.help = help

    def convert(self, argument: str) -> T:
        return convert(argument, self.cls, self.default)
