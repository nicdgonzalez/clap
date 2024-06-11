from typing import Iterable, Iterator

from .token import Token, TokenKind

__all__ = ("Lexer",)


class Lexer:
    """The lexer is responsible for tokenizing the command-line arguments"""

    def __init__(self, input: Iterable[str]) -> None:
        # Create a copy of the input.
        self._input = input[slice(0, None, 1)]

    @property
    def input(self) -> Iterable[str]:
        """Represents the command-line arguments passed to the program"""
        return self._input

    def __iter__(self) -> Iterator[Token]:
        return LexerIterator(self)


class LexerIterator:
    def __init__(self, lexer: Lexer, /) -> None:
        self.input = lexer.input
        self.position = 0

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        try:
            literal = self.input[self.position]
        except IndexError:
            raise StopIteration
        else:
            self.position += 1

        return Token(kind=TokenKind.from_string(literal), literal=literal)

    def peek(self) -> Token | None:
        """Get the next token without advancing the iterator.

        Returns
        -------
        Token:
            The next token produced by the lexer.
        None:
            We hit the end of the iterator; there are no more tokens left.
        """
        before = self.position

        try:
            return next(self)
        except StopIteration:
            return None
        finally:
            self.position = before
