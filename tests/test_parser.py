import pytest

from clap.parser import Lexer, Parser, Token, TokenKind


def test_lexer() -> None:
    lexer = Lexer(
        args=[
            "--verbose",
            "-q",
            "--input=./input.css",
            "--output",
            "./public/output.css",
            "-rf",
            "-2",
            "--",
            "./src/main.c",
            "-",
            "-j8",
        ]
    )

    tokens = iter(lexer)
    tokens_expected = iter(
        (
            Token(kind=TokenKind.LONG, literal="--verbose"),
            Token(kind=TokenKind.SHORT, literal="-q"),
            Token(kind=TokenKind.LONG, literal="--input=./input.css"),
            Token(kind=TokenKind.LONG, literal="--output"),
            Token(kind=TokenKind.ARGUMENT, literal="./public/output.css"),
            Token(kind=TokenKind.SHORT, literal="-rf"),
            Token(kind=TokenKind.ARGUMENT, literal="-2"),
            Token(kind=TokenKind.ESCAPE, literal="--"),
            Token(kind=TokenKind.ARGUMENT, literal="./src/main.c"),
            Token(kind=TokenKind.STDIN, literal="-"),
            Token(kind=TokenKind.SHORT, literal="-j8"),
        )
    )

    for actual, expected in zip(tokens, tokens_expected):
        assert actual.kind == expected.kind
        assert actual.literal == expected.literal

    # Ensure all tokens were checked.
    with pytest.raises(StopIteration):
        _ = next(tokens)

    # Ensure all expected tokens were checked.
    with pytest.raises(StopIteration):
        _ = next(tokens_expected)
