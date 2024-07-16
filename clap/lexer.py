from __future__ import annotations

import dataclasses
import enum
from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator


class TokenType(enum.IntEnum):
    ARGUMENT = enum.auto()
    LONG = enum.auto()
    SHORT = enum.auto()
    ESCAPE = enum.auto()
    STDIN = enum.auto()


@dataclasses.dataclass
class Token:
    type: TokenType
    value: str

    @property
    def is_negative_number(self) -> bool:
        return self.value.startswith("-") and self.value[1:].isnumeric()

    @property
    def is_option(self) -> bool:
        return self.type in (TokenType.LONG, TokenType.SHORT)

    def from_long_option(self) -> tuple[str, str]:
        remainder = self.value.removeprefix("--")

        if "=" in remainder:
            flag, value = remainder.split("=", maxsplit=1)
            return flag, value

        return remainder, ""

    def from_short_option(self) -> Generator[tuple[str, str], None, None]:
        remainder = self.value.removeprefix("-")

        if remainder:
            for index, option in enumerate(remainder):
                try:
                    next_char = remainder[index + 1]
                except IndexError:
                    next_char = ""

                if next_char.isnumeric():
                    start_of_number = index + 1
                    yield (option, remainder[start_of_number:])
                    break
                elif next_char == "=":
                    option, value = remainder[index:].split("=", maxsplit=1)
                    yield (option, value)
                    break
                else:
                    assert option.isalpha()
                    yield (option, "")
        else:
            # This is stdin. There are no flags.
            yield "", ""


def get_token_type(arg: str) -> TokenType:
    if arg.startswith("--"):
        return TokenType.ESCAPE if arg == "--" else TokenType.LONG
    elif arg.startswith("-"):
        remainder = arg[1:]

        if not remainder:
            return TokenType.STDIN
        elif remainder[0].isalpha():
            return TokenType.SHORT
        elif remainder[0].isnumeric():
            return TokenType.ARGUMENT
        else:
            raise NotImplementedError
    else:
        return TokenType.ARGUMENT


class Lexer:

    def __init__(self, args: list[str], /):
        if len(args) < 1:
            raise ValueError(
                "sys.argv[0] is always the path to the executable file. "
                "If you are using your own list of args instead of sys.argv, "
                "insert an empty string at index 0."
            )

        self._args = args[1:]
        self._cursor = 0

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        try:
            arg = self._args[self._cursor]
        except IndexError:
            raise StopIteration
        else:
            self._cursor += 1

        return Token(get_token_type(arg), arg)

    def peek(self) -> Token | None:
        original = self._cursor

        try:
            return next(self)
        except StopIteration:
            return None
        finally:
            self._cursor = original
