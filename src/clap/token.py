import enum


class TokenKind(enum.IntEnum):
    LONG = enum.auto()
    SHORT = enum.auto()
    ARGUMENT = enum.auto()
    ESCAPE = enum.auto()
    STDIN = enum.auto()

    @classmethod
    def from_str(cls, value: str, /) -> "TokenKind":
        if value.startswith("--"):
            return cls.ESCAPE if value == "--" else cls.LONG
        elif value.startswith("-"):
            if (remainder := value[1:]) == "":
                return cls.STDIN
            elif remainder[0].isalpha():
                return cls.SHORT
            elif remainder[0].isnumeric():
                return cls.ARGUMENT  # Value is a negative number, not a flag.
            else:
                raise NotImplementedError
        else:
            return cls.ARGUMENT


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

    def is_long(self) -> bool:
        return self.literal.startswith("--") and not self.is_escape()

    def is_short(self) -> bool:
        return (
            self.literal.startswith("-")
            and not self.is_stdin()
            and not self.literal.startswith("--")
        )

    def as_long_option(self) -> tuple[str, str | None]:
        remainder = self.literal.removeprefix("--")

        if "=" in remainder:
            key, value = remainder.split("=", maxsplit=1)
            return key, value
        else:
            return remainder, None

    def as_short_option(self) -> list[tuple[str, str | None]]:
        remainder = self.literal.removeprefix("-")

        if remainder == "":
            return [("", None)]

        stack: list[tuple[str, str | None]] = []

        for index, key in enumerate(remainder):
            try:
                next = remainder[index + 1]
            except IndexError:
                next = ""

            if next == "" or next.isalpha():
                # It's empty or the next flag; ignore and let
                # the next iteration handle it.
                stack.append((key, None))
            elif next.isnumeric():
                # Values can be part of the stack if:
                #
                # - it is the last option, and
                # - the last option is asking for a numeric value.
                #
                # E.g., this is okay: `-abc123`, but `-c123ba` is not.
                offset = index + 1
                value = remainder[offset:]
                stack.append((key, value))
            elif next == "=":
                # Handle stacks like: `-abc=1024`, `-n=8`, etc.
                key, value = remainder[index:].split("=", maxsplit=1)
                stack.append((key, value))
                break  # We read to the end of the stack.
            else:
                raise NotImplementedError()

        return stack

    def as_argument(self) -> str:
        return self.literal
