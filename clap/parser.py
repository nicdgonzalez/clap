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
from .lexer import Lexer, Token, TokenType

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Callable, Optional, Union

__all__ = ("ParsedArgs", "Parser")

_log = logging.getLogger(__name__)


@dataclasses.dataclass
class ParsedArgs:
    command: Union[HasCommands, CallableArgument]
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
        token_map: Dict[TokenType, Callable[..., None]]
        token_map = {
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
        assert isinstance(self.ctx.command, HasOptions)
        flag, value = token.from_long_option()

        try:
            option = self.ctx.command.all_options[token.snake_case]
        except KeyError:
            raise InvalidOptionError(self.ctx.command, token)

        if not value:
            if option.target_type is bool:
                value = str(not option.default)
            elif (
                next_token is not None
                and next_token.is_argument
                and option.n_args.maximum > 0
            ):
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
        assert isinstance(self.ctx.command, HasOptions)

        for flag, value in token.from_short_option():
            try:
                option = self.ctx.command.all_options[flag]
            except KeyError:
                raise InvalidOptionError(self.ctx.command, token)

            new_token_type = TokenType.LONG
            new_value = "--{}".format(option.name.replace("_", "-"))

            if value:
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
                # even though the check already proves it is a HasCommands...
                command = cast(HasCommands, self.ctx.command)
                raise InvalidCommandError(command, token)

            return
        else:
            assert isinstance(self.ctx.command, HasPositionalArgs)
            index = len(self.ctx.args)

            try:
                argument = self.ctx.command.all_positionals[index]
            except IndexError:
                raise TooManyArgumentsError(self.ctx.command, token)

            converted_value = argument.convert(value)
            self.ctx.args.append(converted_value)
