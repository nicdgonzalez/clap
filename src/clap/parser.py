from __future__ import annotations

import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Iterator, Sequence, cast

from colorize import Colorize

from . import abc
from .abc import (
    SupportsConvert,
    SupportsHelpMessage,
    SupportsOptions,
    SupportsPositionalArguments,
    SupportsSubcommands,
)
from .errors import ArgumentError, MissingRequiredArgumentError, UserError
from .help import HelpFormatter
from .lexer import Lexer, LexerIterator
from .option import Option
from .positional import PositionalArgument
from .sentinel import MISSING
from .token import Token, TokenKind
from .util import snake_case

if TYPE_CHECKING:
    from .application import Application
    from .script import Script


@dataclasses.dataclass
class ParsedArgs:
    command: SupportsSubcommands | SupportsPositionalArguments
    args: list[PositionalArgument[Any]] = dataclasses.field(
        default_factory=list
    )
    kwargs: dict[str, Option[Any]] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class ParserContext:
    command: SupportsSubcommands | SupportsPositionalArguments
    tokens: Iterator[Token]
    result: ParsedArgs
    buffer: list[ParsedArgs]


# TODO: Documentation.
def parse(
    app: Application | Script[Any],
    /,
    input: Sequence[str] = sys.argv[slice(1, None, 1)],
    *,
    formatter: HelpFormatter = HelpFormatter(),
) -> Any:
    try:
        results = _parse_app(app=app, input=input)
    except ArgumentError as exc:
        print(Colorize("error").red() + ":", exc, file=sys.stderr)
        sys.exit(1)

    assert len(results) > 0, len(results)
    for result in results:
        if result.kwargs.pop("help", False):
            assert isinstance(result.command, SupportsHelpMessage)
            help_message = result.command.get_help_message().render(formatter)
            print(help_message)
            return None

        if (
            isinstance(result.command, SupportsSubcommands)
            and not result.command.invoke_without_subcommand
        ):
            continue

        # Ensure all arguments are accounted for.
        try:
            assert isinstance(result.command, SupportsOptions)
            required_args_count = len(
                tuple(
                    filter(
                        lambda a: a.default_value is MISSING,
                        (
                            result.command.positional_arguments
                            if hasattr(result.command, "positional_arguments")
                            else ()
                        ),
                    )
                )
            )

            if len(result.args) < required_args_count:
                raise MissingRequiredArgumentError()

            for option in result.command.options:
                if (
                    option.default_value is MISSING
                    and snake_case(option.name) not in result.kwargs.keys()
                ):
                    raise MissingRequiredArgumentError()
        except MissingRequiredArgumentError:
            assert isinstance(result.command, SupportsHelpMessage)
            usage = result.command.usage.render(formatter)
            print(usage, file=sys.stderr)
            sys.exit(1)

        try:
            assert callable(result.command)
            retval: Any = result.command(*result.args, **result.kwargs)
        except UserError as exc:
            print(Colorize("error").red() + ":", exc, file=sys.stderr)
            sys.exit(1)

    return retval


def _parse_app(
    app: Application | Script[Any],
    input: Sequence[str],
) -> list[ParsedArgs]:
    lexer = Lexer(input=input)
    tokens = iter(lexer)
    results: list[ParsedArgs] = []
    ctx = ParserContext(
        command=app,
        tokens=tokens,
        buffer=results,
        result=ParsedArgs(command=app),
    )

    for token in tokens:
        next_token = cast(LexerIterator, tokens).peek()
        _handle_token(ctx=ctx, token=token, next_token=next_token)

    # Don't forget to save the state of the current command as well.
    ctx.buffer.append(ctx.result)

    return ctx.buffer


def _handle_token(
    ctx: ParserContext, *, token: Token, next_token: Token | None
) -> None:
    match token.kind:
        case TokenKind.LONG:
            _handle_token_long(ctx=ctx, token=token, next_token=next_token)
        case TokenKind.SHORT:
            _handle_token_short(ctx=ctx, token=token, next_token=next_token)
        case TokenKind.ARGUMENT:
            _handle_token_argument(ctx=ctx, token=token)
        case TokenKind.ESCAPE:
            _handle_token_escape(ctx=ctx)
        case TokenKind.STDIN:
            raise NotImplementedError
        case _:
            raise AssertionError(f"unreachable: {token.kind}")


def _handle_token_long(
    ctx: ParserContext, *, token: Token, next_token: Token | None
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
            raise ArgumentError(f"expected value for option {option.name!r}")
        else:
            value_raw = next_token.as_argument()
            # Advance the iterator since we used the next token.
            _ = next(ctx.tokens)
    else:
        value_raw = option_raw.value

    ctx.result.kwargs[option.parameter_name] = option.convert(value_raw)


def _handle_token_short(
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

        literal = f"--{option.name.replace('-', '_')}"

        if value != "":
            literal += f"={value}"

        _handle_token_long(
            ctx=ctx,
            token=Token(kind=TokenKind.LONG, literal=literal),
            next_token=next_token,
        )


def _handle_token_argument(
    ctx: ParserContext,
    *,
    token: Token,
) -> None:
    argument_raw = token.as_argument()

    match ctx.command:
        case abc.SupportsSubcommands():
            try:
                command = ctx.command.all_subcommands[argument_raw]
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
        case abc.SupportsPositionalArguments():
            # Get argument object from command based on position.
            index = len(ctx.result.args)
            try:
                argument = ctx.command.positional_arguments[index]
            except IndexError as exc:
                expected = len(ctx.command.positional_arguments)
                actual = len(ctx.result.args) + 1
                plural = "" if expected == 1 else "s"
                raise ArgumentError(
                    f"expected {expected} argument{plural}, got {actual}"
                ) from exc
            else:
                # Append to arguments if there is enough room.
                value = argument.target_type(argument_raw)
                ctx.result.args.append(value)
        case _:
            raise NotImplementedError


def _handle_token_escape(ctx: ParserContext) -> None:
    match ctx.command:
        case abc.SupportsSubcommands():
            # TODO: Handle ESCAPE token for SupportsSubcommands
            ...
        case abc.SupportsPositionalArguments():
            for token in ctx.tokens:
                _handle_token_argument(ctx=ctx, token=token)
        case _:
            raise NotImplementedError
