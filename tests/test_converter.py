import unittest
from typing import Literal

from clap.converter import convert
from clap.errors import ArgumentError


class TestConverter(unittest.TestCase):
    def test_literal(self) -> None:
        priority = Literal["low", "medium", "high"]

        self.assertEqual(convert(argument="low", converter=priority), "low")

        with self.assertRaises(expected_exception=ArgumentError):
            convert(argument="1", converter=priority)

    def test_union(self) -> None:
        t = int | bool
        self.assertEqual(convert(argument="1", converter=t), 1)
        self.assertEqual(convert(argument="true", converter=t), True)

        with self.assertRaises(expected_exception=ArgumentError):
            convert(argument="treu", converter=t)

    def test_generic(self) -> None:
        pass
