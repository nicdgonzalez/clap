from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, cast

from .abc import CallableArgument, HasCommands, HasOptions
from .errors import (
    InvalidCommandError,
    InvalidOptionError,
    TooManyArgumentsError,
)
from .lexer import Lexer

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Callable, Optional

    from .lexer import Token, TokenType

__all__ = ("ParsedArgs", "Parser")


@dataclasses.dataclass
class ParsedArgs:
    command: Optional[CallableArgument] = None
    args: List[Any] = dataclasses.field(default_factory=list)
    kwargs: Dict[str, Any] = dataclasses.field(default_factory=dict)


class Parser:

    def __init__(self, args: List[str], /) -> None:
        self.lexer = Lexer(args[:])
        self.deferred: List[Token] = []
        self.ctx = ParsedArgs()

    def parse(self) -> ParsedArgs:
        for token in self.lexer:
            self.handle_token(token)

        # TODO: fill in options that have default values set

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
            option = command.all_options.get(token.snake_case)
        except KeyError:
            raise InvalidOptionError(self.ctx.command, token)

        if value == "":
            valid_next_token = next_token and next_token.is_argument

            if option.target_type is bool:
                value = str(not option.default)
            elif valid_next_token and option.n_args.maximum > 0:
                value = next_token.from_argument()
            else:
                pass  # value stays an empty string

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

        if self.ctx.command is None or isinstance(self.ctx.command, HasCommands):
            try:
                self.ctx.command = self.ctx.command.all_commands[value]
            except KeyError:
                raise InvalidCommandError(self.ctx.command, token)

            return

        index = len(self.ctx.args)

        try:
            argument = self.ctx.command.all_positionals[index]
        except IndexError:
            raise TooManyArgumentsError(self.ctx.command, token)

        converted_value = argument.convert(value)
        self.ctx.args.append(converted_value)
