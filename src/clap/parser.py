import dataclasses
import inspect
import os
import sys
from collections.abc import Iterable, Iterator, Sequence
from typing import Any, Self

from .command import Command, Schema
from .sentinel import MISSING
from .token import Token, TokenKind


class Lexer(Iterable[Token]):
    """Performs lexical analysis on the input arguments.

    Parameters
    ----------
    args
        Command-line arguments (excluding argv[0])
    """

    def __init__(self, argv: Sequence[str]) -> None:
        self._argv = argv

    def __iter__(self) -> "LexerIterator":
        return LexerIterator(self._argv)


class LexerIterator(Iterator[Token]):
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


@dataclasses.dataclass()
class ParseContext:
    schema: Schema
    index: int


class Parser:
    """Defines the grammar for command-line arguments.

    Parameters
    ----------
    tokens
        Iterator over the tokenized command-line arguments
    """

    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens = tokens

        self.token: Token | None = None
        self.advance()  # Set value for `token`.

    def advance(self) -> None:
        try:
            self.token = next(self.tokens)
        except StopIteration:
            self.token = None

    def is_kind(self, expected: TokenKind) -> bool:
        if self.token is None:
            return False

        return self.token.kind == expected

    def parse[T](self, cls: type[T]) -> T:
        annotations = inspect.get_annotations(cls)
        schema = Schema.from_annotations(annotations)

        results: dict[str, Any] = {}
        index = 0  # For tracking positional-only arguments.
        ctx = ParseContext(schema, index)

        while self.token is not None:
            match self.token.kind:
                case TokenKind.LONG:
                    key, value = self.parse_long_option(ctx)
                    results[key] = value

                case TokenKind.SHORT:
                    for key, value in self.parse_short_option(ctx):
                        results[key] = value

                case TokenKind.ARGUMENT:
                    key, value = self.parse_argument(ctx)
                    results[key] = value

                case TokenKind.ESCAPE:
                    pass

                case TokenKind.STDIN:
                    pass

                case _:
                    raise NotImplementedError()

        return dataclasses.dataclass(cls)(**results)

    def parse_long_option(
        self,
        ctx: ParseContext,
    ) -> tuple[str, Any]:
        assert self.token is not None
        key, value = self.token.as_long_option()
        self.advance()

        try:
            option = ctx.schema.options[key]
        except KeyError as err:
            raise RuntimeError(f"unknown option: {key}") from err

        # TODO: Storing the value is the default behavior; I want to allow
        # custom actions, like `Action::Count`.

        # If `bool`, the option being present *is* the value.
        if option.cls is bool:
            return option.name, not option.default

        # Check if the next token contains the value for this option.
        if value is None:
            if self.is_kind(TokenKind.ARGUMENT):
                value = self.token.as_argument()
                self.advance()
            else:
                raise RuntimeError(f"expected value for option: {key}")

        return option.name, option.convert(value)

    def parse_short_option(
        self,
        ctx: ParseContext,
    ) -> list[tuple[str, Any]]:
        results: list[tuple[str, Any]] = []

        assert self.token is not None
        stack = self.token.as_short_option()
        self.advance()

        # The last flag follows different rules, so we'll handle it separately.
        last_key, last_value = stack.pop()

        for key, value in stack:
            try:
                option = ctx.schema.options[key]
            except KeyError as err:
                raise RuntimeError(f"unknown error: {key}") from err

            if option.cls is bool:
                results.append((option.name, not option.default))
                continue
            elif option.default is not MISSING:
                results.append((option.name, option.default))
                continue
            else:
                # TODO: Add "Hint: try using `-{key} VALUE` instead"
                raise RuntimeError(
                    f"cannot stack flags that require an argument: {key}"
                )

        try:
            last_option = ctx.schema.options[last_key]
        except KeyError as err:
            raise RuntimeError(f"unknown error: {last_key}") from err

        if last_option.cls is bool:
            results.append((last_option.name, not last_option.default))
            return results

        if last_value is None:
            if self.is_kind(TokenKind.ARGUMENT):
                last_value = self.token.as_argument()
                self.advance()
            else:
                raise RuntimeError(f"expected value for option: {last_key}")

        results.append((last_option.name, last_option.convert(last_value)))
        return results

    def parse_argument(
        self,
        ctx: ParseContext,
    ) -> tuple[str, Any]:
        assert self.token is not None
        value = self.token.as_argument()
        self.advance()

        try:
            argument = ctx.schema.arguments[ctx.index]
        except IndexError as err:
            if ctx.schema.subcommand is not None:
                try:
                    ctx.schema = ctx.schema.subcommand[1].subcommands[value]
                    ctx.index = 0
                except KeyError as err:
                    raise RuntimeError(f"unknown subcommand: {value}") from err
                else:
                    pass
            else:
                expected = len(ctx.schema.arguments)
                actual = ctx.index + 1

                raise RuntimeError(
                    f"expected {expected} argument(s), got {actual}"
                ) from err
        else:
            ctx.index += 1

        return argument.name, argument.convert(value)


class ArgumentParser(Command):
    def __init_subclass__(
        cls,
        program: str = os.path.basename(sys.argv[0]),
        version: str | None = None,
        add_help: bool = True,
        about: str | None = None,
        long_about: str | None = None,
        after_help: str | None = None,
    ) -> None:
        super().__init_subclass__()
        cls.program = program
        cls.version = version
        cls.add_help = add_help
        cls.about = about
        cls.long_about = long_about
        cls.after_help = after_help

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
        lexer = Lexer(argv=argv)
        parser = Parser(tokens=iter(lexer))
        return parser.parse(cls)
