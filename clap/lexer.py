from __future__ import annotations

import enum
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from builtins import list as List
    from builtins import tuple as Tuple
    from typing import Iterator, Optional

_log = logging.getLogger(__name__)


class TokenType(enum.IntEnum):
    LONG = enum.auto()
    SHORT = enum.auto()
    ARGUMENT = enum.auto()
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

    def from_long_option(self) -> Tuple[str, str]:
        # 2 is the length of the leading '--'.
        remainder = self.value[2:] if self.is_long_option else self.value[:]

        if "=" in remainder:
            flag, value = remainder.split("=", maxsplit=1)
            return flag, value

        return remainder, ""

    def from_short_option(self) -> Iterator[Tuple[str, str]]:
        # 1 is the length of the leading '-'.
        remainder = self.value[1:] if self.is_short_option else self.value[:]

        if not remainder:
            # This is stdin. There are no flags.
            yield "", ""
            raise StopIteration

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

        raise StopIteration

    def from_argument(self) -> str:
        return self.value[:]


class Cursor:
    def __init__(self, begin: int = 0, *, end: int) -> None:
        self._begin = begin
        self._end = end
        self._position = begin

    @property
    def begin(self) -> int:
        return self._begin

    @property
    def end(self) -> int:
        return self._end

    @property
    def position(self) -> int:
        return self._position

    @position.setter
    def position(self, value: int) -> None:
        if not (self.begin <= value <= self.end):
            raise IndexError(
                "position {} not in range {}..{}".format(
                    value, self.begin, self.end
                )
            )

        self._position = value

    def advance(self, n: int = 1, /) -> None:
        self.position += n

    def retreat(self, n: int = 1, /) -> None:
        self.advance(-n)

    def seek(self, position: int, /) -> None:
        self.advance(position - self.position)


class Lexer:
    def __init__(self, args: List[str], /) -> None:
        self._args = args[:]  # create a copy of the original
        self._cursor = Cursor(end=len(self._args))

    @property
    def args(self) -> List[str]:
        return self._args[:]

    @property
    def cursor(self) -> Cursor:
        return self._cursor

    @property
    def begin(self) -> int:
        return 0

    @property
    def end(self) -> int:
        return len(self._args)

    @property
    def escape(self) -> int:
        try:
            return self._args.index("--")
        except ValueError:
            return self.end

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        try:
            arg = self.args[self.cursor.position]
            self.cursor.advance(1)
        except IndexError:
            raise StopIteration

        if self.cursor.position - 1 > self.escape or not arg.startswith("-"):
            return Token(TokenType.ARGUMENT, arg)
        else:
            return Token(self.get_token_type(arg), arg)

    def peek(self) -> Optional[Token]:
        original = self.cursor.position

        try:
            token = next(self)
        except StopIteration:
            return None
        finally:
            self.cursor.seek(original)

        return token

    def get_token_type(self, arg: str, /) -> TokenType:
        if arg.startswith("--"):
            return TokenType.ESCAPE if arg == "--" else TokenType.LONG
        elif arg.startswith("-"):
            remainder = arg[1:]

            if not remainder:
                return TokenType.STDIN
            elif remainder[0].isalpha():
                return TokenType.SHORT
            elif remainder.isnumeric():
                return TokenType.ARGUMENT
            else:
                raise NotImplementedError
        else:
            return TokenType.ARGUMENT
