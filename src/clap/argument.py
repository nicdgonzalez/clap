from .convert import convert
from .sentinel import MISSING


class Argument[T]:
    def __init__(
        self,
        name: str,
        tp: type[T],
        default: T | MISSING = MISSING,
        help: str | None = None,
    ) -> None:
        self.name = name
        self.tp = tp
        self.default = default
        self.help = help

    def convert(self, argument: str) -> T:
        return convert(argument, self.tp, self.default)
