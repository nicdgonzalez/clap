"""
Lexer
=====

The lexer is responsible for converting the raw command-line arguments into a
list of tokens that can be parsed by the parser.

"""
from __future__ import annotations

import enum
from typing import Iterable, NamedTuple


class TokenType(enum.IntEnum):
    """Represents the type of token."""

    # A long option (e.g. `--help`).
    LONG_OPTION = enum.auto()
    # A short option (e.g. `-h`).
    SHORT_OPTION = enum.auto()
    # An argument (e.g. `foo`).
    ARGUMENT = enum.auto()


class Token(NamedTuple):
    """Represents a token."""

    type: TokenType
    value: str


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
                f"Position not in range {self.begin}..{self.end}: {value}."
            )
        self._position = value


class Lexer:
    def __init__(self, __args: list[str], /) -> None:
        self._args = __args.copy()

    @property
    def escape(self) -> int:
        return self._args.index("--") if "--" in self._args else self.end

    @property
    def begin(self) -> int:
        return 0

    @property
    def end(self) -> int:
        return len(self._args)

    def cursor(self) -> Cursor:
        return Cursor(begin=self.begin, end=self.end)

    def tokens(self, cursor: Cursor, /, peek: bool = False) -> Iterable[Token]:
        while cursor.position < self.end:
            argument = self.get_raw_argument(cursor)

            if cursor.position > self.escape:
                yield Token(TokenType.ARGUMENT, argument)
            elif argument.startswith("--"):
                yield Token(TokenType.LONG_OPTION, argument)
            elif argument.startswith("-"):
                for option in argument[1:]:
                    yield Token(TokenType.SHORT_OPTION, option)
            else:
                yield Token(TokenType.ARGUMENT, argument)

            self.advance(cursor) if not peek else None

    def get_raw_argument(self, cursor: Cursor) -> str:
        return self._args[cursor.position]

    def advance(self, cursor: Cursor, n: int = 1) -> None:
        cursor.position += n

    def retreat(self, cursor: Cursor, n: int = 1) -> None:
        self.advance(cursor, -n)

    def seek(self, cursor: Cursor, position: int) -> None:
        self.advance(cursor, position - cursor.position)

    def valid_cursor(self, cursor: Cursor) -> bool:
        return (
            cursor.begin >= self.begin
            and cursor.end <= self.end
            and cursor.begin <= cursor.position <= cursor.end
        )
