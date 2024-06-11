import enum
import operator
from typing import NamedTuple

from .errors import ArgumentError

__all__ = (
    "RawArgument",
    "RawOption",
    "Token",
    "TokenKind",
)


class TokenKind(enum.IntEnum):
    LONG = enum.auto()
    SHORT = enum.auto()
    ARGUMENT = enum.auto()
    ESCAPE = enum.auto()
    STDIN = enum.auto()

    @classmethod
    def from_string(cls, value: str, /) -> "TokenKind":
        if value.startswith("--"):
            return cls.ESCAPE if value == "--" else cls.LONG
        elif value.startswith("-"):
            remainder = value[slice(1, None, 1)]

            if remainder == "":
                return cls.STDIN
            elif remainder[0].isalpha():
                return cls.SHORT
            elif remainder[0].isnumeric():
                return cls.ARGUMENT
            else:
                raise NotImplementedError
        else:
            return cls.ARGUMENT


class RawOption(NamedTuple):
    key: str
    value: str

    def __eq__(self, o: object) -> bool:
        if isinstance(o, RawOption):
            return self.key == o.key and self.value == o.value

        return NotImplemented

    def __ne__(self, o: object) -> bool:
        result = operator.eq(self, o)
        return NotImplemented if result is NotImplemented else not result


class RawArgument(str):
    pass


class Token:
    def __init__(self, kind: TokenKind, literal: str) -> None:
        self.kind = kind
        self.literal = literal

    def is_escape(self) -> bool:
        return self.literal == "--"

    def is_stdin(self) -> bool:
        return self.literal == "-"

    def is_negative_number(self) -> bool:
        return (
            len(self.literal) > 1
            and self.literal.startswith("-")
            and self.literal[1:].isnumeric()
        )

    def is_option(self) -> bool:
        return (
            len(self.literal) > 1
            and self.literal.startswith("-")
            and not self.is_negative_number()
        )

    def is_argument(self) -> bool:
        # All tokens are technically arguments; this is just a convenience
        # method so you don't have to import `TokenKind` yourself.
        return self.kind == TokenKind.ARGUMENT

    def as_long_option(self) -> RawOption:
        remainder = self.literal.removeprefix("--")

        if "=" in remainder:
            key, value = remainder.split("=", maxsplit=1)
            return RawOption(key=key, value=value)
        else:
            return RawOption(key=remainder, value="")

    def as_short_option(self) -> tuple[RawOption, ...]:
        remainder = self.literal.removeprefix("-")

        if remainder == "":
            return (RawOption(key="", value=""),)

        options: list[RawOption] = []

        # Short options are stackable (e.g., `-abc` is OK). Here, we break
        # apart the stack to return each option individually.
        for index, key in enumerate(remainder):
            try:
                next_char = remainder[index + 1]
            except IndexError:
                next_char = ""

            if next_char == "" or next_char.isalpha():
                # `next_char` represents the next option, so ignore and let
                # the next iteration handle it.
                options.append(RawOption(key=key, value=""))
            elif next_char.isnumeric():
                # Values can be a part of the stack if:
                #
                # - only the last option accepts a value, and
                # - the last option is asking for a numberic value.
                #
                # E.g., this is okay: `-abc123`; but this is not: `-c123ba`.
                value = remainder[slice(index + 1, None, 1)]
                print(value)

                if not value.isnumeric():
                    raise ArgumentError(
                        f"expected value for {key!r} to be numeric"
                    )

                options.append(RawOption(key=key, value=value))
                break  # We already read to the end of `remainder`.
            elif next_char == "=":
                # Handle stacks like: `-abc=1024`, `-n=8`, etc.
                # fmt: off
                key, value = (
                    remainder[slice(index, None, 1)]
                    .split("=", maxsplit=1)
                )
                # fmt: on
                options.append(RawOption(key=key, value=value))
                break  # We already read to the end of `remainder`.
            else:
                # Symbols and other non-alphanumeric values.
                raise NotImplementedError(f"unexpected option: {key}")

        return tuple(options)

    def as_argument(self) -> RawArgument:
        return RawArgument(self.literal)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Token):
            return self.kind == o.kind and self.literal == o.literal

        return NotImplemented

    def __ne__(self, o: object) -> bool:
        result = operator.eq(self, o)
        return NotImplemented if result is NotImplemented else not result
