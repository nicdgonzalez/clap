from __future__ import annotations

import copy
import dataclasses
import logging
from typing import TYPE_CHECKING

from .abc import CallableArgument, HasCommands, HasOptions, HasPositionalArgs
from .commands import Command
from .errors import (
    InvalidCommandError,
    InvalidOptionError,
    TooManyArgumentsError,
)
from .lexer import Lexer, Token, TokenType
from .utils import MISSING

if TYPE_CHECKING:
    from typing import Any

    from .arguments import Option
    from .core import Application, Script

__all__ = ("ParsedArgs", "Parser")

_log = logging.getLogger(__name__)


@dataclasses.dataclass
class ParsedArgs:
    command: Script | HasCommands | CallableArgument
    args: list[Any] = dataclasses.field(default_factory=list)
    kwargs: dict[str, Any] = dataclasses.field(default_factory=dict)

    def copy(self) -> ParsedArgs:
        return ParsedArgs(
            command=copy.copy(self.command),
            args=copy.copy(self.args),
            kwargs=copy.copy(self.kwargs),
        )


class Parser:

    def __init__(
        self, args: list[str], /, command: Application | Script
    ) -> None:
        self.lexer = Lexer(args)
        self.ctx = ParsedArgs(command=command)
        self.queue: list[ParsedArgs] = []

    def parse(self) -> list[ParsedArgs]:
        for token in self.lexer:
            self.handle_token(token)

        self.queue.append(self.ctx.copy())

        return self.queue

    def handle_token(self, token: Token) -> None:
        next_token = self.lexer.peek()

        match token.type:
            case TokenType.LONG:
                if next_token and next_token.type != TokenType.ARGUMENT:
                    next_token = None

                self.handle_token_long(token, next_token=next_token)
            case TokenType.SHORT:
                if next_token and next_token.type != TokenType.ARGUMENT:
                    next_token = None

                self.handle_token_short(token, next_token=next_token)
            case TokenType.ARGUMENT:
                self.handle_token_argument(token)
            case TokenType.ESCAPE:
                self.handle_token_escape(next_token)
            case TokenType.STDIN:
                # TODO: I'm not sure how to properly handle this case
                raise NotImplementedError
            case _:
                raise NotImplementedError

        return

    def handle_token_long(
        self, token: Token, *, next_token: Token | None
    ) -> None:
        flag, value = token.from_long_option()
        assert isinstance(self.ctx.command, HasOptions)

        try:
            option: Option = self.ctx.command.all_options[flag]
        except KeyError as exc:
            raise InvalidOptionError(self.ctx.command, token) from exc

        if value == "":
            if next_token is not None and option.n_args.maximum > 0:
                assert next_token.type == TokenType.ARGUMENT
                value = next_token.value
                _ = next(self.lexer)
            elif option.target_type is bool:
                value = str(not option.default)
            else:
                pass  # no argument provided, or no argument required

        _log.debug("flag={}, value={}".format(flag, value))

        converted_value = option.convert(value)
        self.ctx.kwargs[option.snake_case] = converted_value

    def handle_token_short(
        self, token: Token, *, next_token: Token | None
    ) -> None:
        assert isinstance(self.ctx.command, HasOptions)

        for flag, value in token.from_short_option():
            try:
                option: Option = self.ctx.command.all_options[flag]
            except KeyError as exc:
                raise InvalidOptionError(self.ctx.command, token) from exc

            new_type = TokenType.LONG
            new_value = "--{}".format(option.kebab_case)

            if value:
                new_value += "={}".format(value)

            new_token = Token(new_type, new_value)
            self.handle_token_long(new_token, next_token=next_token)

    def handle_token_argument(self, token: Token) -> None:
        if isinstance(self.ctx.command, HasCommands):
            self.handle_token_escape(next_token=None)

            try:
                self.ctx.command = self.ctx.command.all_commands[token.value]
            except KeyError as exc:
                raise InvalidCommandError(self.ctx.command, token) from exc  # type: ignore
            else:
                return
        else:
            assert isinstance(self.ctx.command, HasPositionalArgs)
            index = len(self.ctx.command.all_positionals) - 1

            try:
                positional = self.ctx.command.all_positionals[index]
            except IndexError as exc:
                raise TooManyArgumentsError(
                    self.ctx.command, (*self.ctx.args, token.value)
                ) from exc
            else:
                converted_value = positional.convert(token.value)
                self.ctx.args.append(converted_value)

    def handle_token_escape(self, next_token: Token | None) -> None:
        if isinstance(self.ctx.command, HasCommands):
            assert isinstance(self.ctx.command, HasOptions)

            for option in self.ctx.command.all_options.values():
                kwarg = option.snake_case

                if kwarg in self.ctx.kwargs or option.default is MISSING:
                    continue

                self.ctx.kwargs[kwarg] = option.default

            for option_name in self.ctx.kwargs.keys():
                # This should be safe, since we are reversing how we got here
                option = self.ctx.command.all_options[
                    option_name.replace("_", "-")
                ]
                option.validate_requires(self.ctx.kwargs.keys())
                option.validate_conflicts(self.ctx.kwargs.keys())

            self.queue.append(self.ctx.copy())

            if next_token is None:
                return

            try:
                next_command = self.ctx.command.all_commands[next_token.value]
            except KeyError as exc:
                raise InvalidCommandError(
                    self.ctx.command, next_token
                ) from exc
            else:
                self.ctx = ParsedArgs(command=next_command)
                _ = next(self.lexer)
        elif isinstance(self.ctx.command, Command):
            # Consume the rest of the tokens as arguments
            for token in self.lexer:
                self.handle_token_argument(token)
