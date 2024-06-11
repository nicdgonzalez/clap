import dataclasses
import sys
from typing import Iterable, cast

from .abc import HasArguments, HasCommands
from .argument import Argument
from .errors import ArgumentError
from .lexer import Lexer, LexerIterator
from .option import Option
from .token import Token, TokenKind


class ParserResult:
    def __init__(
        self,
        command: HasCommands | HasArguments,
    ) -> None:
        self._command = command
        self._args: list[Argument] = []
        self._kwargs: dict[str, Option] = {}

    @property
    def command(self) -> HasCommands | HasArguments:
        return self._command

    @property
    def args(self) -> list[Argument]:
        return self._args

    @property
    def kwargs(self) -> dict[str, Option]:
        return self._kwargs

    def __str__(self) -> str:
        return f"ParserResult(command={self.command.name}, args={self.args}, kwargs={self.kwargs})"  # noqa: E501


@dataclasses.dataclass
class ParserContext:
    def __init__(self, command: HasCommands | HasArguments) -> None:
        self._command = command
        self.result = ParserResult(command=self._command)
        # We need to keep track of each callable argument's state so we can
        # process everything at the end. For example, with the command:
        #
        #   `git --verbose clone --depth=1 <url>`
        #
        # We want to link `--verbose` to `git` and `--depth=1` to `clone`.
        # To do this, we'll create a new `ParserResult` for each level
        # in the command tree and save the previous one to a buffer.
        self.buffer: list[ParserResult] = []

    @property
    def command(self) -> HasCommands | HasArguments:
        return self._command

    @command.setter
    def command(self, value: HasCommands | HasArguments) -> None:
        self.buffer.append(self.result)
        self._command = value
        self.result = ParserResult(command=self._command)


def parse(
    interface: HasCommands | HasArguments,
    /,
    input: Iterable[str] = sys.argv[slice(1, None, 1)],
) -> tuple[ParserResult, ...]:
    lexer = Lexer(input=input)
    tokens = iter(lexer)

    ctx = ParserContext(command=interface)

    for token in tokens:
        next_token = cast(LexerIterator, tokens).peek()
        handle_token(ctx=ctx, token=token, next_token=next_token)

        # if isinstance(obj, Option):
        #     result.kwargs[obj.name] = obj
        # elif isinstance(obj, Argument):
        #     result.args.append(obj)
        # else:
        #     raise NotImplementedError

    return ctx.buffer


# TODO: Reconsider managing the state of the program via a mutable context.
# Currently questioning whether passing around context is necessary if I could
# just maintain state using a class...


def handle_token(
    ctx: ParserContext,
    *,
    token: Token,
    next_token: Token | None,
) -> Option | Argument:
    match token.kind:
        case TokenKind.LONG:
            handle_token_long(
                ctx=ctx,
                token=token,
                next_token=next_token,
            )
        case TokenKind.SHORT:
            handle_token_short(
                ctx=ctx,
                token=token,
                next_token=next_token,
            )
        case TokenKind.ARGUMENT:
            handle_token_argument(
                ctx=ctx,
                token=token,
                next_token=next_token,
            )
        case TokenKind.ESCAPE:
            raise NotImplementedError
        case TokenKind.STDIN:
            raise NotImplementedError
        case _:
            raise AssertionError(f"unreachable: {token.kind}")


def handle_token_long(
    ctx: ParserContext,
    *,
    token: Token,
    next_token: Token | None,
) -> Option:
    if next_token is not None and next_token.kind != TokenKind.ARGUMENT:
        next_token = None

    option_raw = token.as_long_option()

    try:
        option = ctx.command.options[option_raw.key]
    except KeyError as exc:
        raise ArgumentError(f"unknown option: {option_raw.key}") from exc

    if option.cls is not bool and option_raw.value == "":
        # Check if next token is the value.
        print(
            "flag expects a value but value is currently empty, checking if next token is the value"
        )

    print("handling long option token", option_raw)

    raise NotImplementedError


def handle_token_short(
    ctx: ParserContext,
    *,
    token: Token,
    next_token: Token | None,
) -> Option:
    if next_token is not None and next_token.kind != TokenKind.ARGUMENT:
        next_token = None

    print("handling short option token")

    raise NotImplementedError


def handle_token_argument(
    ctx: ParserContext,
    *,
    token: Token,
    next_token: Token | None,
) -> Argument | None:
    argument_raw = token.as_argument()

    if isinstance(ctx.command, HasCommands):
        try:
            command = ctx.command.commands[argument_raw]
        except KeyError as exc:
            raise ArgumentError(
                f"{argument_raw!r} is not a valid command"
            ) from exc
        else:
            ctx.command = command
    elif isinstance(ctx.command, HasArguments):
        # Get argument object from command based on position.
        index = len(ctx.result.args)
        try:
            argument = ctx.command.arguments[index]
        except IndexError:
            expected = len(ctx.command.arguments)
            actual = len(ctx.result.args) + 1
            raise ArgumentError(f"expected {expected} arguments, got {actual}")
        else:
            # Append to arguments if there is enough room.
            value = argument.cls(argument)
            ctx.result.args.append(value)
    else:
        raise NotImplementedError


def handle_token_escape(
    ctx: ParserContext,
    *,
    token: Token,
    next_token: Token | None,
) -> Argument:
    print("handling escape token")
    raise NotImplementedError
