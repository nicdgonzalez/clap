import unittest

from clap.lexer import Lexer
from clap.token import RawArgument, RawOption, Token, TokenKind


class TestLexer(unittest.TestCase):
    def test_tokens(self) -> None:
        lexer = Lexer(
            input=["--debug", "--host=127.0.0.1", "-p", "25565", "-abc"]
        )
        tokens = iter(lexer)
        expected_tokens = (
            Token(kind=TokenKind.LONG, literal="--debug"),
            Token(kind=TokenKind.LONG, literal="--host=127.0.0.1"),
            Token(kind=TokenKind.SHORT, literal="-p"),
            Token(kind=TokenKind.ARGUMENT, literal="25565"),
            Token(kind=TokenKind.SHORT, literal="-abc"),
        )

        for index, token in enumerate(tokens):
            self.assertEqual(token, expected_tokens[index])

    def test_as_long_option(self) -> None:
        lexer = Lexer(input=["--host=0.0.0.0", "--port", "19132", "--verbose"])
        tokens = iter(lexer)
        expected_options = (
            (RawOption(key="host", value="0.0.0.0")),
            (RawOption(key="port", value="")),
            (RawArgument("19132")),
            (RawOption(key="verbose", value="")),
        )

        for index, token in enumerate(tokens):
            if token.is_option():
                assert token.literal.startswith("--"), token.literal
                self.assertEqual(
                    token.as_long_option(), expected_options[index]
                )
            elif token.kind == TokenKind.ARGUMENT:
                self.assertEqual(token.as_argument(), expected_options[index])
            else:
                raise AssertionError("unreachable")

    def test_as_short_option(self) -> None:
        lexer = Lexer(
            input=["-h=0.0.0.0", "-p", "19132", "-v", "-abc123", "-def"]
        )
        tokens = iter(lexer)
        expected_options = (
            (RawOption(key="h", value="0.0.0.0"),),
            (RawOption(key="p", value=""),),
            RawArgument("19132"),
            (RawOption(key="v", value=""),),
            (
                RawOption(key="a", value=""),
                RawOption(key="b", value=""),
                RawOption(key="c", value="123"),
            ),
            (
                RawOption(key="d", value=""),
                RawOption(key="e", value=""),
                RawOption(key="f", value=""),
            ),
        )

        for index, token in enumerate(tokens):
            if token.is_option():
                assert token.literal.startswith("-"), token.literal
                self.assertEqual(
                    token.as_short_option(), expected_options[index]
                )
            elif token.kind == TokenKind.ARGUMENT:
                self.assertEqual(token.as_argument(), expected_options[index])
            else:
                raise AssertionError("unreachable")

    def test_as_argument(self) -> None:
        lexer = Lexer(input=["git", "pull", "origin", "main"])
        tokens = iter(lexer)
        expected_arguments = (
            RawArgument("git"),
            RawArgument("pull"),
            RawArgument("origin"),
            RawArgument("main"),
        )
        for index, token in enumerate(tokens):
            self.assertEqual(token.as_argument(), expected_arguments[index])
