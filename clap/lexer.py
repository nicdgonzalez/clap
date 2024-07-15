from __future__ import annotations

import enum
from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator


class TokenType(enum.IntEnum):
    PROGRAM = 1
    ARGUMENT = enum.auto()
    LONG = enum.auto()
    SHORT = enum.auto()
    ESCAPE = enum.auto()
    STDIN = enum.auto()


class Token:

    def __init__(self, token_type: TokenType, value: str) -> None:
        self._token_type = token_type
        self._value = value

    @property
    def token_type(self) -> TokenType:
        return self._token_type

    @property
    def value(self) -> str:
        return self._value

    @property
    def snake_case(self) -> str:
        return self.value.lstrip("-").replace("-", "_")

    @property
    def kebab_case(self) -> str:
        return self.value.lstrip("-").replace("_", "-")

    @property
    def is_escape(self) -> bool:
        return self.token_type == TokenType.ESCAPE

    @property
    def is_stdin(self) -> bool:
        return self.token_type == TokenType.STDIN

    @property
    def is_option(self) -> bool:
        return self.token_type in (TokenType.LONG, TokenType.SHORT)

    @property
    def is_long_option(self) -> bool:
        return self.token_type == TokenType.LONG

    @property
    def is_short_option(self) -> bool:
        return self.token_type == TokenType.SHORT

    @property
    def is_negative_number(self) -> bool:
        return (
            self.token_type == TokenType.ARGUMENT
            and self.value.startswith("-")
            and self.value[1:].isnumeric()
        )

    @property
    def is_argument(self) -> bool:
        return self.token_type == TokenType.ARGUMENT

    def from_long_option(self) -> tuple[str, str]:
        # 2 is the length of the leading '--'.
        remainder = self.value[2:] if self.is_long_option else self.value[:]

        if "=" in remainder:
            flag, value = remainder.split("=", maxsplit=1)
            return flag, value

        return remainder, ""

    def from_short_option(self) -> Generator[tuple[str, str], None, None]:
        # 1 is the length of the leading '-'.
        remainder = self.value[1:] if self.is_short_option else self.value[:]

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

    def from_argument(self) -> str:
        return self.value[:]


class Lexer:

    def __init__(self, args: list[str], /):
        if len(args) < 1:
            raise ValueError(
                "sys.argv[0] is always the program name. Insert a placeholder "
                "at index 0 if you are using a custom list for `args`"
            )

        self._args = args
        self._cursor = 0

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        if self._cursor == 0:
            arg = self._args[self._cursor]
            self._cursor += 1
            return Token(TokenType.PROGRAM, arg)

        try:
            arg = self._args[self._cursor]
        except IndexError:
            raise StopIteration
        else:
            self._cursor += 1

            if self._cursor - 1 == 0:
                return Token(TokenType.PROGRAM, arg)

        return Token(self.get_token_type(arg), arg)

    def peek(self) -> Token | None:
        original = self._cursor

        try:
            return next(self)
        except StopIteration:
            return None
        finally:
            self._cursor = original

    def get_token_type(self, arg: str) -> TokenType:
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
