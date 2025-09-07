from __future__ import annotations

import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Iterator, Sequence

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
from .group import Group
from .help import HelpFormatter
from .lexer import Lexer
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
    tokens: Iterator[Token]
    state: ParsedArgs
    buffer: list[ParsedArgs] = dataclasses.field(default_factory=list)


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

    retval: Any = None

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
            # NOTE: If no subcommands are passed, the loop ends without
            # ever defining `retval`.
            continue

        # Ensure all arguments are accounted for.
        try:
            assert isinstance(result.command, SupportsOptions)
            args = (
                result.command.positional_arguments
                if isinstance(result.command, SupportsPositionalArguments)
                else ()
            )
            required_args = filter(lambda a: a.default_value is MISSING, args)
            required_args_count = len(tuple(required_args))

            if len(result.args) < required_args_count:
                raise MissingRequiredArgumentError()

            for option in result.command.options:
                if (
                    option.default_value is MISSING
                    and snake_case(option.name) not in result.kwargs.keys()
                ):
                    raise MissingRequiredArgumentError()
        except MissingRequiredArgumentError:
            # NOTE: This *could* be a good assertion, if maybe the docstring
            # mentioned all the things we are expecting.
            #
            # TODO: This is probably not a good assertion.
            assert isinstance(result.command, SupportsHelpMessage)
            usage = result.command.usage.render(formatter)
            print(usage, file=sys.stderr)
            # TODO: Exiting the program is probably not the best idea.
            # Maybe throw an exception instead.
            sys.exit(1)

        try:
            assert callable(result.command)
            retval = result.command(*result.args, **result.kwargs)
        except UserError as exc:
            print(Colorize("error").red() + ":", exc, file=sys.stderr)
            # TODO: Exiting the program is probably not the best idea.
            # Maybe throw an exception instead.
            sys.exit(1)
        else:
            pass
    else:
        if (
            isinstance(result.command, SupportsSubcommands)
            and not result.command.invoke_without_subcommand
        ):
            assert isinstance(result.command, SupportsHelpMessage)
            help_message = result.command.get_help_message().render(formatter)
            print(help_message)
            sys.exit(1)

    # TODO: Add to the function docstring that the function will
    # return whatever is returned from the "`main`" function.
    return retval


def _parse_app(
    app: Application | Script[Any],
    input: Sequence[str],
) -> list[ParsedArgs]:
    lexer = Lexer(input=input)
    tokens = iter(lexer)
    assert isinstance(app, SupportsOptions)
    assert isinstance(app, (SupportsSubcommands, SupportsPositionalArguments))
    ctx = ParserContext(
        tokens=tokens,
        state=ParsedArgs(command=app),
        buffer=[],
    )

    for token in tokens:
        next_token = tokens.peek()
        _handle_token(ctx=ctx, token=token, next_token=next_token)
    else:
        # Out of tokens; save the state of the last command.
        ctx.buffer.append(ctx.state)

    return ctx.buffer


def _handle_token(
    ctx: ParserContext, *, token: Token, next_token: Token | None
) -> None:
    match token.kind:
        case TokenKind.LONG:
            assert token.is_long_option()
            _handle_token_long(ctx=ctx, token=token, next_token=next_token)
        case TokenKind.SHORT:
            assert token.is_short_option()
            _handle_token_short(ctx=ctx, token=token, next_token=next_token)
        case TokenKind.ARGUMENT:
            assert token.is_argument()
            _handle_token_argument(ctx=ctx, token=token)
        case TokenKind.ESCAPE:
            assert token.is_escape()
            _handle_token_escape(ctx=ctx)
        case TokenKind.STDIN:
            assert token.is_stdin()
            raise NotImplementedError
        case _:
            raise AssertionError(f"unreachable: {token.kind}")


def _handle_token_long(
    ctx: ParserContext, *, token: Token, next_token: Token | None
) -> None:
    if next_token is None or next_token.kind != TokenKind.ARGUMENT:
        # The next token is not a possible value for the current option.
        next_token = None

    assert token.is_long_option()
    option_raw = token.as_long_option()

    try:
        assert isinstance(ctx.state.command, SupportsOptions)
        option = ctx.state.command.all_options[option_raw.key]
    except KeyError as exc:
        raise ArgumentError(f"unknown option: {option_raw.key}") from exc

    assert isinstance(option, SupportsConvert)

    if option_raw.value == "":
        if option.target_type is bool:
            value_raw = str(not option.default_value)
        elif next_token is None:
            raise ArgumentError(f"expected value for option {option.name!r}")
        else:
            assert next_token.is_argument()
            value_raw = next_token.as_argument()
            # Advance the iterator since we used the next token.
            _ = next(ctx.tokens)
    else:
        value_raw = option_raw.value

    ctx.state.kwargs[option.parameter_name] = option.convert(value_raw)


def _handle_token_short(
    ctx: ParserContext,
    *,
    token: Token,
    next_token: Token | None,
) -> None:
    assert token.is_short_option()
    # For each short flag, expand it into its long form and then re-handle it.
    for key, value in token.as_short_option():
        try:
            assert isinstance(ctx.state.command, SupportsOptions)
            option = ctx.state.command.all_options[key]
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
    assert token.is_argument()
    argument_raw = token.as_argument()

    match ctx.state.command:
        case abc.SupportsSubcommands():
            try:
                command = ctx.state.command.all_subcommands[argument_raw]
            except KeyError as exc:
                raise ArgumentError(
                    f"{argument_raw!r} is not a valid command"
                ) from exc
            else:
                # Save the state of the previous command in the buffer.
                ctx.buffer.append(ctx.state)
                # Create new state for the current command.
                ctx.state = ParsedArgs(command=command)
        case abc.SupportsPositionalArguments():
            # Get argument object from command based on position.
            index = len(ctx.state.args)
            try:
                argument = ctx.state.command.positional_arguments[index]
            except IndexError as exc:
                expected = len(ctx.state.command.positional_arguments)
                actual = len(ctx.state.args) + 1
                plural = "" if expected == 1 else "s"
                raise ArgumentError(
                    f"expected {expected} argument{plural}, got {actual}"
                ) from exc
            else:
                # Append to arguments if there is enough room.
                value = argument.target_type(argument_raw)
                ctx.state.args.append(value)
        case _:
            raise NotImplementedError


def _handle_token_escape(ctx: ParserContext) -> None:
    match ctx.state.command:
        case abc.SupportsSubcommands():
            # TODO: Handle ESCAPE token for SupportsSubcommands
            ...
        case abc.SupportsPositionalArguments():
            for token in ctx.tokens:
                _handle_token_argument(ctx=ctx, token=token)
        case _:
            raise NotImplementedError
