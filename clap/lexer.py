"""
Lexer
=====

This module implements the lexer, which is responsible for converting the raw
command-line arguments into a sequence of tokens to be interpreted by the
parser.

"""
from __future__ import annotations

import enum
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from builtins import list as List
    from builtins import tuple as Tuple
    from typing import Iterator, Optional


class TokenType(enum.IntEnum):
    """Enumeration of all possible token types."""

    LONG_OPTION = enum.auto()
    SHORT_OPTION = enum.auto()
    ARGUMENT = enum.auto()
    ESCAPE = enum.auto()
    STDIN = enum.auto()


class Token:
    """Represents a token output by the :class:`.Lexer`.

    Attributes
    ----------
    token_type : :class:`.TokenType`
        An identifier for the token.
    value : :class:`str`
        The raw contents of the command-line argument.
    """

    def __init__(self, token_type: TokenType, value: str) -> None:
        self.token_type = token_type
        self.value = value

    @property
    def as_kebab_case(self) -> str:
        """Return the value in kebab-case. The value should already be in
        kebab-case, so this just strips the leading ``--`` or ``-``.

        Returns
        -------
        :class:`str`
            The value in kebab-case.
        """
        return self.value.lstrip("-")

    @property
    def as_snake_case(self) -> str:
        """Return the value in snake_case. This also strips the leading ``--``
        or ``-``.

        Returns
        -------
        :class:`str`
            The value in snake_case.
        """
        return self.value.lstrip("-").replace("-", "_")

    @property
    def is_escape(self) -> bool:
        """Return whether this token is the end of options token.

        Returns
        -------
        :class:`bool`
            Whether this token is the end of options token.
        """
        return self.token_type == TokenType.ESCAPE and self.value == "--"

    @property
    def is_stdin(self) -> bool:
        """Return whether this token is the standard input token.

        Returns
        -------
        :class:`bool`
            Whether this token is the standard input token.
        """
        return self.token_type == TokenType.STDIN and self.value == "-"

    @property
    def is_option(self) -> bool:
        """Return whether this token is an option.

        Returns
        -------
        :class:`bool`
            Whether this token is an option.
        """
        valid_token = self.token_type in (
            TokenType.LONG_OPTION,
            TokenType.SHORT_OPTION,
        )

        return valid_token and self.value.startswith("-")

    @property
    def is_long_option(self) -> bool:
        """Return whether this token is a long option.

        Returns
        -------
        :class:`bool`
            Whether this token is a long option.
        """
        return (
            self.token_type == TokenType.LONG_OPTION
            and self.value.startswith("--")
            and not self.is_escape
        )

    @property
    def is_short_option(self) -> bool:
        """Return whether this token is a short option.

        Returns
        -------
        :class:`bool`
            Whether this token is a short option.
        """
        return (
            self.token_type == TokenType.SHORT_OPTION
            and self.value.startswith("-")
            and not self.is_stdin
        )

    @property
    def is_negative_number(self) -> bool:
        """Return whether this token is a negative number.

        Returns
        -------
        :class:`bool`
            Whether this token is a negative number.
        """
        return (
            self.token_type == TokenType.ARGUMENT
            and self.value.startswith("-")
            and not self.is_stdin
            and self[1:].isnumeric()
        )

    @property
    def is_argument(self) -> bool:
        """Return whether this token is an argument.

        Returns
        -------
        :class:`bool`
            Whether this token is an argument.
        """
        return self.token_type == TokenType.ARGUMENT and (
            self.is_negative_number or not self.is_option
        )

    def from_long_option(self) -> Tuple[str, str]:
        """Get the option name and value from a long option.

        Returns
        -------
        :class:`tuple` of :class:`str`
            The option name and value.
        """
        # 2 is the length of the leading '--'.
        remainder = self.value[2:] if self.is_long_option else self.value[:]

        if "=" in remainder:
            flag, value = remainder.split("=", maxsplit=1)
            return flag, value

        return remainder, ""

    def from_short_option(self) -> Iterator[Tuple[str, str]]:
        """Get an iterator over the short option names and values.

        Notes
        -----
        Because short options can be grouped together, this method returns an
        iterator over the option names and values. In groups, only the last
        option can have a value. For example, the following command-line
        arguments::

            -abc=foo,bar

        Would yield the following::

            ("a", "")
            ("b", "")
            ("c", "foo,bar")

        If the last option takes a numerical value, it can be concatenated
        with the option::

            -abc123

        Would yield the following::

            ("a", "")
            ("b", "")
            ("c", "123")

        Yields
        ------
        :class:`tuple` of :class:`str`
            The option name and value.
        """
        # 1 is the length of the leading '-'.
        remainder = self.value[1:] if self.is_short_option else self.value[:]

        if not remainder:
            # This is stdin. There are no flags.
            return (("", ""),)

        for index, option in enumerate(remainder):
            try:
                next_char = remainder[index + 1]
            except IndexError:
                next_char = ""

            if next_char.isnumeric():
                start_of_number = index + 1
                yield option, remainder[start_of_number:]
                break
            elif next_char == "=":
                option, value = remainder[index:].split("=", maxsplit=1)
                yield option, value
                break
            else:
                assert option.isalpha()
                yield option, ""

    def from_argument(self) -> str:
        """Get the value as it was passed on the command-line.

        Returns
        -------
        :class:`str`
            A copy of the value as it was passed on the command-line.
        """
        return self.value[:]


class Cursor:
    """Represents the current position in the command-line arguments.

    Attributes
    ----------
    begin : int
        The lower bound of the cursor.
    end : int
        The upper bound of the cursor.
    position : int
        The current position of the cursor.
    """

    def __init__(self, begin: int = 0, *, end: int) -> None:
        self._begin = begin
        self._end = end
        self._position = begin

    @property
    def begin(self) -> int:
        """The lower bound of the cursor."""
        return self._begin

    @property
    def end(self) -> int:
        """The upper bound of the cursor."""
        return self._end

    @property
    def position(self) -> int:
        """The current position of the cursor."""
        return self._position

    @position.setter
    def position(self, value: int) -> None:
        """Set the current position of the cursor.

        Parameters
        ----------
        value : int
            The new position of the cursor.

        Raises
        ------
        ValueError
            If the new position is not in the range [begin, end].
        """
        if not (self.begin <= value <= self.end):
            raise IndexError(
                f"Position {value} not in range {self.begin}..{self.end}"
            )

        self._position = value

    def advance(self, n: int = 1, /) -> None:
        """Advance the cursor by n positions.

        Parameters
        ----------
        n : int
            The number of positions to advance the cursor by.

        Raises
        ------
        ValueError
            If the new position is not in the range [begin, end].
        """
        self.position += n

    def retreat(self, n: int = 1, /) -> None:
        """Retreat the cursor by n positions.

        Parameters
        ----------
        n : int
            The number of positions to retreat the cursor by.

        Raises
        ------
        ValueError
            If the new position is not in the range [begin, end].
        """
        self.advance(-n)

    def seek(self, position: int) -> None:
        """Seek the cursor to a new position.

        Parameters
        ----------
        position : int
            The new position of the cursor.

        Raises
        ------
        ValueError
            If the new position is not in the range [begin, end].
        """
        self.advance(position - self.position)


class Lexer:
    """Converts the raw command-line arguments into a sequence of tokens
    to be interpreted by the parser.

    Attributes
    ----------
    args : :class:`list` of :class:`str`
        The command-line arguments to tokenize.
    cursor : :class:`Cursor`
        The current position in the command-line arguments.
    begin : :class:`int`
        The lower bound of the cursor.
    end : :class:`int`
        The upper bound of the cursor.
    escape : :class:`int`
        The position of the escape token. If the escape token is not present,
        this is set to :attr:`end`.
    """

    def __init__(self, args: List[str] = sys.argv, /) -> None:
        self._args = args[:]
        self._cursor = Cursor(end=len(args))
        self._argument_map = {
            "--": self._maybe_long_option,
            "-": self._maybe_short_option,
        }

    @property
    def args(self) -> List[str]:
        """The command-line arguments to tokenize.

        Returns
        -------
        :class:`list` of :class:`str`
            A shallow copy of the internal list of command-line arguments.
        """
        return self._args.copy()

    @property
    def cursor(self) -> Cursor:
        """The current position in the command-line arguments.

        Returns
        -------
        :class:`.Cursor`
            A shallow copy of the internal cursor.
        """
        return self._cursor

    @property
    def begin(self) -> int:
        """The lower bound of the cursor.

        Returns
        -------
        :class:`int`
            The lower bound of the cursor.
        """
        return 0

    @property
    def end(self) -> int:
        """The upper bound of the cursor.

        Returns
        -------
        :class:`int`
            The upper bound of the cursor.
        """
        return len(self._args)

    @property
    def escape(self) -> int:
        """The position of the escape token. If the escape token is not
        present, this is set to :attr:`end`.

        Returns
        -------
        :class:`int`
            The position of the escape token.
        """
        try:
            return self._args.index("--")
        except ValueError:
            return self.end

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        try:
            argument = self._args[self.cursor.position]
            self._cursor.advance(1)
        except IndexError:
            raise StopIteration

        if self._cursor.position - 1 > self.escape:
            return Token(TokenType.ARGUMENT, argument)

        for condition, token_type in self._argument_map.items():
            if argument.startswith(condition):
                return Token(token_type(argument), argument)

        return Token(TokenType.ARGUMENT, argument)

    def peek(self) -> Optional[Token]:
        """Get the next token without advancing the cursor.

        Returns
        -------
        :class:`.Token`
            The next token.
        """
        original_position = self.cursor.position

        try:
            token = next(self)
        except StopIteration:
            return None
        finally:
            self.cursor.seek(original_position)

        return token

    def _maybe_long_option(self, argument: str, /) -> TokenType:
        """Get the token type of an argument that starts with ``--``.

        Parameters
        ----------
        argument : :class:`str`
            The argument to check.

        Returns
        -------
        :class:`.TokenType`
            The token type of the argument.
        """
        assert argument.startswith("--"), argument
        return TokenType.ESCAPE if argument == "--" else TokenType.LONG_OPTION

    def _maybe_short_option(self, argument: str, /) -> TokenType:
        """Get the token type of an argument that starts with ``-``.

        Parameters
        ----------
        argument : :class:`str`
            The argument to check.

        Returns
        -------
        :class:`.TokenType`
            The token type of the argument.
        """
        assert argument.startswith("-"), argument

        remainder = argument[1:]

        if not remainder:
            return TokenType.STDIN
        elif remainder[0].isalpha():
            return TokenType.SHORT_OPTION
        elif remainder.isnumeric():
            return TokenType.ARGUMENT
        else:
            raise NotImplementedError
