from __future__ import annotations

import dataclasses
import logging
from typing import TYPE_CHECKING, cast

from .abc import CallableArgument, HasCommands, HasOptions, HasPositionalArgs
from .errors import (
    InvalidCommandError,
    InvalidOptionError,
    TooManyArgumentsError,
)
from .lexer import Lexer, TokenType

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Callable, Optional, Union

    from .lexer import Token

__all__ = ("ParsedArgs", "Parser")

_log = logging.getLogger(__name__)


@dataclasses.dataclass
class ParsedArgs:
    command: Union[HasCommands, CallableArgument] = None
    args: List[Any] = dataclasses.field(default_factory=list)
    kwargs: Dict[str, Any] = dataclasses.field(default_factory=dict)


class Parser:

    def __init__(
        self, args: List[str], /, command: Union[HasCommands, CallableArgument]
    ) -> None:
        self.lexer = Lexer(args[:])
        self.deferred: List[Token] = []
        self.ctx = ParsedArgs(command=command)

    def parse(self) -> ParsedArgs:
        for token in self.lexer:
            _log.debug(
                "parsing token: ({}, {!r})".format(
                    token.token_type, token.value
                )
            )
            self.handle_token(token)

        self.handle_deferred_tokens()

        # TODO: fill in options that have default values set
        # (required to do the next part)

        # TODO: ensure that each option accurately handles requires/conflicts

        return self.ctx

    def handle_token(self, token: Token) -> None:
        if token.is_option:
            # because we may not know what command we are working with yet,
            # all options are deferred until the very end... (not the best
            # solution, but works for now)
            self.deferred.append(token)

            try:
                next_token = self.lexer.peek()
            except StopIteration:
                next_token = None

            if next_token is None or next_token.is_option:
                return

            if next_token.is_argument:
                self.deferred.append(next_token)
                _ = next(self.lexer)
        elif token.is_argument:
            self.handle_token_argument(token, next_token=None)
        elif token.is_escape:
            return
        elif token.is_stdin:
            raise NotImplementedError
        else:
            raise NotImplementedError

    def handle_deferred_tokens(self) -> None:
        token_map: Dict[TokenType, Callable[Token, Optional[Token]]] = {
            TokenType.LONG: self.handle_token_long,
            TokenType.SHORT: self.handle_token_short,
            TokenType.ARGUMENT: self.handle_token_argument,
        }

        while self.deferred:
            token = self.deferred.pop(0)
            next_token = self.deferred[0] if self.deferred else None
            token_map[token.token_type](token, next_token=next_token)

    def handle_token_long(
        self,
        token: Token,
        *,
        next_token: Optional[Token],
    ) -> None:
        assert self.ctx.command is not None, self.ctx.command
        command = cast(HasOptions, self.ctx.command)
        flag, value = token.from_long_option()

        try:
            option = command.all_options[token.snake_case]
        except KeyError:
            raise InvalidOptionError(self.ctx.command, token)

        if value == "":
            valid_next_token = next_token and next_token.is_argument

            if option.target_type is bool:
                value = str(not option.default)
            elif valid_next_token and option.n_args.maximum > 0:
                value = next_token.from_argument()
                _ = self.deferred.pop(0)
            else:
                pass  # value stays an empty string

        _log.debug("flag: {}, value: {}".format(flag, value))

        converted_value = option.convert(value)
        self.ctx.kwargs[option.name] = converted_value

    def handle_token_short(
        self,
        token: Token,
        *,
        next_token: Optional[Token],
    ) -> None:
        assert self.ctx.command is not None, self.ctx.command
        command = cast(HasOptions, self.ctx.command)

        for flag, value in token.from_short_option():
            try:
                option = command.all_options[flag]
            except KeyError:
                raise InvalidOptionError(self, token)

            new_token_type = TokenType.LONG
            new_value = "--{}".format(option.replace("_", "-"))

            if value is not None:
                new_value += "={}".format(value)

            new_token = Token(new_token_type, new_value)
            self.handle_token_long(new_token, next_token=next_token)

    def handle_token_argument(
        self,
        token: Token,
        *,
        next_token: Optional[Token],
    ) -> None:
        value = token.from_argument()

        if isinstance(self.ctx.command, HasCommands):
            try:
                self.ctx.command = self.ctx.command.all_commands[value]
            except KeyError:
                raise InvalidCommandError(self.ctx.command, token)

            return
        else:
            assert isinstance(self.ctx.command, HasPositionalArgs)
            command = cast(HasPositionalArgs, self.ctx.command)
            index = len(self.ctx.args)
            _log.debug(
                "index: {}, all_positionals: {}".format(
                    index,
                    ",".join(obj.name for obj in command.all_positionals),
                )
            )

            try:
                argument = self.ctx.command.all_positionals[index]
            except IndexError:
                raise TooManyArgumentsError(self.ctx.command, token)

            converted_value = argument.convert(value)
            self.ctx.args.append(converted_value)
