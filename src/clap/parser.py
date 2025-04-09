from __future__ import annotations

import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Iterator, Sequence, cast

from . import abc
from .abc import (
    HasName,
    SupportsArguments,
    SupportsCommands,
    SupportsConvert,
    SupportsOptions,
)
from .argument import Argument
from .errors import ArgumentError
from .lexer import Lexer, LexerIterator
from .option import Option
from .token import Token, TokenKind

if TYPE_CHECKING:
    from .application import Application


@dataclasses.dataclass
class ParsedArgs:
    command: SupportsOptions | SupportsCommands | SupportsArguments
    args: list[Argument[Any]] = dataclasses.field(default_factory=list)
    kwargs: dict[str, Option[Any]] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class ParserContext:
    command: SupportsOptions | SupportsCommands | SupportsArguments
    tokens: Iterator[Token]
    result: ParsedArgs
    buffer: list[ParsedArgs]


class Parser:
    def __init__(self, app: Application) -> None:
        self.app = app

    def parse(
        self, input: Sequence[str] = sys.argv[slice(1, None, 1)]
    ) -> list[ParsedArgs]:
        lexer = Lexer(input=input)
        tokens = iter(lexer)
        results: list[ParsedArgs] = []
        ctx = ParserContext(
            command=self.app,
            tokens=tokens,
            buffer=results,
            result=ParsedArgs(command=self.app),
        )

        for token in tokens:
            next_token = cast(LexerIterator, tokens).peek()
            self.handle_token(ctx=ctx, token=token, next_token=next_token)

        # Save the state of the current command.
        ctx.buffer.append(ctx.result)

        return ctx.buffer

    def handle_token(
        self, ctx: ParserContext, *, token: Token, next_token: Token | None
    ) -> None:
        match token.kind:
            case TokenKind.LONG:
                self.handle_token_long(
                    ctx=ctx, token=token, next_token=next_token
                )
            case TokenKind.SHORT:
                self.handle_token_short(
                    ctx=ctx, token=token, next_token=next_token
                )
            case TokenKind.ARGUMENT:
                self.handle_token_argument(ctx=ctx, token=token)
            case TokenKind.ESCAPE:
                self.handle_token_escape(ctx=ctx)
            case TokenKind.STDIN:
                raise NotImplementedError
            case _:
                raise AssertionError(f"unreachable: {token.kind}")

    def handle_token_long(
        self, ctx: ParserContext, *, token: Token, next_token: Token | None
    ) -> None:
        if next_token is not None and next_token.kind != TokenKind.ARGUMENT:
            next_token = None

        option_raw = token.as_long_option()

        try:
            assert isinstance(ctx.command, SupportsOptions)
            option = ctx.command.all_options[option_raw.key]
        except KeyError as exc:
            raise ArgumentError(f"unknown option: {option_raw.key}") from exc

        assert isinstance(option, SupportsConvert)

        if option_raw.value == "":
            if option.target_type is bool:
                value_raw = str(not option.default_value)
            elif next_token is None or not next_token.is_argument():
                raise ArgumentError(
                    f"expected value for option {option.name!r}"
                )
            else:
                value_raw = next_token.as_argument()
                # Advance the iterator since we used the next token.
                _ = next(ctx.tokens)
        else:
            value_raw = option_raw.value

        # Convert option name to snake_case.
        name = option_raw.key.replace("-", "_")

        ctx.result.kwargs[name] = option.convert(value_raw)

    def handle_token_short(
        self,
        ctx: ParserContext,
        *,
        token: Token,
        next_token: Token | None,
    ) -> None:
        for key, value in token.as_short_option():
            try:
                assert isinstance(ctx.command, SupportsOptions)
                option = ctx.command.all_options[key]
            except KeyError as exc:
                raise ArgumentError(f"unknown option: {key}") from exc

            assert isinstance(option, HasName)
            literal = f"--{option.name.replace('-', '_')}"

            if value != "":
                literal += f"={value}"

            self.handle_token_long(
                ctx=ctx,
                token=Token(kind=TokenKind.LONG, literal=literal),
                next_token=next_token,
            )

    def handle_token_argument(
        self,
        ctx: ParserContext,
        *,
        token: Token,
    ) -> None:
        argument_raw = token.as_argument()

        match ctx.command:
            case abc.SupportsCommands():
                try:
                    command = ctx.command.all_commands[argument_raw]
                except KeyError as exc:
                    raise ArgumentError(
                        f"{argument_raw!r} is not a valid command"
                    ) from exc
                else:
                    # Store the previous command's state in the buffer,
                    # then create new state for the current command.
                    ctx.buffer.append(ctx.result)
                    ctx.result = ParsedArgs(command=command)
                    ctx.command = command
            case abc.SupportsArguments():
                # Get argument object from command based on position.
                index = len(ctx.result.args)
                try:
                    argument = ctx.command.arguments[index]
                except IndexError as exc:
                    expected = len(ctx.command.arguments)
                    actual = len(ctx.result.args) + 1
                    raise ArgumentError(
                        f"expected {expected} arguments, got {actual}"
                    ) from exc
                else:
                    # Append to arguments if there is enough room.
                    value = argument.target_type(argument_raw)
                    ctx.result.args.append(value)
            case _:
                raise NotImplementedError

    def handle_token_escape(self, ctx: ParserContext) -> None:
        match ctx.command:
            case abc.SupportsCommands():
                ...
            case abc.SupportsArguments():
                for token in ctx.tokens:
                    self.handle_token_argument(ctx=ctx, token=token)
            case _:
                raise NotImplementedError
