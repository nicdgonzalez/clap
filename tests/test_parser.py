import unittest

import clap
from clap.parser import parse


class TestParser(unittest.TestCase):
    def test_parser(self) -> None:
        app = clap.Application()

        @app.subcommand()
        def serve(*, host: str, port: int, verbose: bool) -> None:
            print("Serving documentation!")

        result = parse(
            app,
            input=["serve", "--host", "0.0.0.0", "--port=8080", "--verbose"],
        )
        # self.assertEqual(len(result), 1)
