import unittest

from clap.lexer import Lexer, TokenType


class TestLexer(unittest.TestCase):

    def test_explicit_escapes(self) -> None:
        args = (
            ("./example.py", TokenType.PROGRAM),
            ("--verbose", TokenType.LONG),
            ("--", TokenType.ESCAPE),
            ("plugins", TokenType.ARGUMENT),
            ("--", TokenType.ESCAPE),
            ("install", TokenType.ARGUMENT),
            ("--url", TokenType.LONG),
            (
                "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot",
                TokenType.ARGUMENT,
            ),
            ("--", TokenType.ESCAPE),
            ("celestia", TokenType.ARGUMENT),
            ("Geyser-Spigot.jar", TokenType.ARGUMENT),
        )
        lexer = Lexer([a[0] for a in args])

        for token, expected in zip(lexer, [a[1] for a in args]):
            self.assertEqual(token.token_type, expected)

    def test_implicit_escapes(self) -> None:
        args = (
            ("./example.py", TokenType.PROGRAM),
            ("--verbose", TokenType.LONG),
            ("plugins", TokenType.ARGUMENT),
            ("install", TokenType.ARGUMENT),
            ("--url", TokenType.LONG),
            (
                "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot",
                TokenType.ARGUMENT,
            ),
            ("celestia", TokenType.ARGUMENT),
            ("Geyser-Spigot.jar", TokenType.ARGUMENT),
        )
        lexer = Lexer([a[0] for a in args])

        for token, expected in zip(lexer, [a[1] for a in args]):
            self.assertEqual(token.token_type, expected)

    def test_empty_args(self) -> None:
        with self.assertRaises(ValueError):
            Lexer([])
