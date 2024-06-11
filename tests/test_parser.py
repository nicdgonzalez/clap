import unittest

from clap.parser import parse


class TestParser(unittest.TestCase):
    def test_parser(self) -> None:
        result = parse(
            ["serve", "--host", "0.0.0.0", "--port=8080", "--verbose"]
        )
        # self.assertEqual(len(result), 1)
