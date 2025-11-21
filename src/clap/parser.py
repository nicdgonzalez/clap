import dataclasses
import enum
import inspect
import sys
from collections.abc import Iterable, Iterator, Sequence
from typing import Annotated, Any, Self, get_args, get_origin

from .argument import Argument
from .metadata import Help, Long, Short
from .option import Option
from .sentinel import MISSING


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


class Lexer(Iterable[Token]):
    """Performs lexical analysis on the input arguments.

    Parameters
    ----------
    args
        Command-line arguments (excluding argv[0])
    """

    def __init__(self, args: Sequence[str]) -> None:
        self._args = args

    def __iter__(self) -> "LexerIterator":
        return LexerIterator(self._args)


class LexerIterator(Iterator[Token]):
    """Tokenize command-line arguments.

    This iterator implements `PeekableIterator`.
    """

    def __init__(self, args: Sequence[str]):
        self._args = args
        self._index = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Token:
        try:
            literal = self._args[self._index]
        except IndexError:
            raise StopIteration
        else:
            self._index += 1

        return Token(kind=TokenKind.from_str(literal), literal=literal)


class Parser:
    """Defines the grammar for command-line arguments.

    Parameters
    ----------
    tokens
        Iterator over the tokenized command-line arguments
    """

    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens = tokens

        self.current: Token | None = None
        self.next: Token | None = None

        # Advance the iterator twice to set both `current` and `next`.
        self.advance()
        self.advance()

    def advance(self) -> None:
        self.current = self.next

        try:
            self.next = next(self.tokens)
        except StopIteration:
            self.next = None


@dataclasses.dataclass(frozen=True)
class ParseContext:
    arguments: list[Argument[Any]]
    options: dict[str, Option[Any]]


class ArgumentParser:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    @classmethod
    def parse(cls, args: Sequence[str] = sys.argv[1:]) -> Self:
        """Parse the command-line arguments.

        A convenient wrapper over `self.try_parse` except instead of throwing
        an exception on failure, we print the help message to stdout and exit
        the program with exit code 2.

        Parameters
        ----------
        args
            Command-line arguments (excluding `sys.argv[0]`)
        """
        try:
            return cls.try_parse(argv=args)
        except Exception:
            # Standard exit code for failure due to bad command-line arguments.
            # TODO: Print the help message.
            sys.exit(2)

    @classmethod
    def try_parse(cls, argv: Sequence[str] = sys.argv[1:], /) -> Self:
        # Parse the ArgumentParser type to determine the valid subcommands,
        # positional arguments, and options.
        annotations = inspect.get_annotations(cls)

        ctx = ParseContext(
            arguments=[],
            options={},
        )

        for name, tp in annotations.items():
            # TODO: handle enum subcommands
            if get_origin(tp) is Annotated:
                arg_type, *metadata = get_args(tp)

                is_long = False
                short: Short | None = None
                help: Help | None = None

                for data in metadata:
                    if data is Long:
                        is_long = True
                    elif data is Short:
                        short = Short(name[0])
                    elif isinstance(data, Short):
                        short = data
                    elif isinstance(data, Help):
                        help = data.value

                if is_long or short is not None:
                    option = Option(
                        name=name,
                        tp=arg_type,
                        short=short,
                        default=getattr(cls, name, MISSING),
                        help=help,
                    )

                    if short is not None:
                        if short.value in ctx.options.keys():
                            raise RuntimeError(
                                f"option already exists: {short.value}"
                            )
                        else:
                            assert short.value is not None
                            ctx.options[short.value] = option

                    if name in ctx.options.keys():
                        raise RuntimeError(f"option already exists: {name}")
                    else:
                        ctx.options[name] = option
            else:
                # No annotations; default to positional-only argument.
                ctx.arguments.append(
                    Argument(
                        name=name,
                        tp=tp,
                        default=getattr(cls, name, MISSING),
                        help=None,
                    )
                )

        # Parse the command-line arguments.
        lexer = Lexer(args=argv)
        parser = Parser(tokens=iter(lexer))

        # Results to return to the user.
        index = 0
        kwargs: dict[str, Any] = {}

        while parser.current is not None:
            current = parser.current
            next = parser.next

            match parser.current.kind:
                case TokenKind.LONG:
                    if next is not None and next.kind != TokenKind.ARGUMENT:
                        next = None  # Not a potential value for this option.

                    key_raw, value_raw = current.as_long_option()

                    try:
                        option = ctx.options[key_raw]
                    except KeyError as err:
                        raise RuntimeError(
                            f"unknown option: {key_raw}"
                        ) from err

                    if value_raw is None:
                        if option.tp is bool:
                            value_raw = str(not option.default)
                        elif next is None:
                            raise RuntimeError(
                                f"expected value for option: {key_raw}"
                            )
                        else:
                            assert next is not None
                            assert next.kind == TokenKind.ARGUMENT, next.kind
                            value_raw = next.as_argument()
                            parser.advance()  # Used the next token.
                    else:
                        pass

                    kwargs[option.name] = option.convert(value_raw)
                    parser.advance()

                case TokenKind.SHORT:
                    for key, value in current.as_short_option():
                        try:
                            option = ctx.options[key]
                        except KeyError as err:
                            raise RuntimeError(
                                f"unknown error: {key}"
                            ) from err

                        literal = f"--{option.name.replace('_', '-')}"

                        if value is not None:
                            literal += f"={value}"

                        # Replace the short flag with its long version.
                        current = Token(kind=TokenKind.LONG, literal=literal)

                        if (
                            next is not None
                            and next.kind != TokenKind.ARGUMENT
                        ):
                            # Not a potential value for this option.
                            next = None

                        key_raw, value_raw = current.as_long_option()

                        if value_raw is None:
                            if option.tp is bool:
                                value_raw = str(not option.default)
                            elif next is None:
                                raise RuntimeError(
                                    f"expected value for option: {key_raw}"
                                )
                            else:
                                # TODO: Shouldn't use `next` unless we know we
                                # are the last element of the stack.
                                assert next is not None
                                assert next.kind == TokenKind.ARGUMENT, (
                                    next.kind
                                )
                                value_raw = next.as_argument()
                                parser.advance()  # Used the next token.
                        else:
                            pass

                        kwargs[option.name] = option.convert(value_raw)

                    parser.advance()

                case TokenKind.ARGUMENT:
                    value_raw = current.as_argument()

                    # TODO:
                    # if len(ctx.arguments) == 1 and isinstance(ctx.arguments[0], Subcommand):  # noqa: E501
                    #     # check against subcommand enum
                    #     ...

                    try:
                        argument = ctx.arguments[index]
                    except IndexError as err:
                        expected = len(ctx.arguments)
                        actual = index + 1
                        plural = "" if expected == 1 else "s"
                        raise RuntimeError(
                            f"expected {expected} argument{plural}, got {actual}"  # noqa: E501
                        ) from err
                    else:
                        value = argument.convert(value_raw)
                        # Even though these are positional-only arguments, we
                        # still send them to the user as keyword arguments so
                        # that the order that the attributes were defined in
                        # doesn't matter.
                        kwargs[argument.name] = value
                        index += 1

                    parser.advance()

                case TokenKind.ESCAPE:
                    pass

                case TokenKind.STDIN:
                    pass

                case _:
                    raise NotImplementedError()

        return cls(**kwargs)
