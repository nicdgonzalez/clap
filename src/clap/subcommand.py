from typing import Any

from .argument import Argument
from .option import Option


class Subcommand:
    def __init__(
        self,
        name: str,
        args: list[Argument[Any]],
        options: dict[str, Option[Any]],
        help: str | None = None,
    ) -> None:
        self.name = name
        self.args = args
        self.options = options
        self.help = help
