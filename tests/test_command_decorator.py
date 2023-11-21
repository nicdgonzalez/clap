import unittest
from typing import Annotated, Any

import clap
from clap.metadata import Conflicts, Short


def test_argument(argument: clap.Argument, expected: dict[str, Any]) -> None:
    """Tests an argument."""
    assert argument.name == expected["name"]
    assert argument.help == expected["help"]
    assert argument.cls == expected["cls"]
    assert argument.default == expected["default"]
    assert argument.range == expected["range"]


def test_option(option: clap.Option, expected: dict[str, Any]) -> None:
    """Tests an option."""
    assert option.name == expected["name"]
    assert option.help == expected["help"]
    assert option.cls == expected["cls"]
    assert option.default == expected["default"]
    assert option.range == expected["range"]
    assert option.short == expected["short"]
    assert option.conflicts == expected["conflicts"]
    assert option.requires == expected["requires"]


def test_short_option_map(
    short_option_map: dict[str, str], expected: dict[str, Any]
) -> None:
    """Tests a short option map."""
    for short, long in short_option_map.items():
        assert short in expected["short_option_map"].keys()
        assert long in expected["short_option_map"].values()


def test_command(command: clap.Command, test: dict[str, Any]) -> None:
    """Tests a command."""
    assert command.name == test["name"]
    assert command.help == test["help"]
    for argument, expected_a in zip(command.arguments, test["arguments"]):
        test_argument(argument, expected_a)
    for option, expected_o in zip(command.options, test["options"]):
        test_option(option, expected_o)
    assert command.short_option_map == test["short_option_map"]


class Test(clap.Parser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            help="A command-line tool for managing servers.",
            epilog="Thank you for using Test!",
            *args,
            **kwargs,
        )

    @clap.command()
    def start(self, server: str, /) -> None:
        """Starts the specified server.

        Parameters
        ----------
        server : str
            The name of the server to start.
        """
        pass

    @clap.command()
    def start_default(self, /, auto_reconnect: bool = False) -> None:
        """Starts the default server.

        Parameters
        ----------
        auto_reconnect : bool, default=False
            Whether to automatically reconnect to the server if it stops.
        """
        pass

    @clap.command(name="stop")
    def not_go(self, server: str, /) -> None:
        """Stops the specified server.

        Parameters
        ----------
        server : str
            The name of the server to stop.
        """
        pass

    @clap.command()
    def setup(
        self,
        /,
        quiet: Annotated[bool, Short("q"), Conflicts("verbose")] = False,
        verbose: Annotated[bool, Short("v"), Conflicts("quiet")] = False,
    ) -> None:
        """Sets up the specified server.

        Parameters
        ----------
        quiet : bool, default=False
            Whether to suppress all output.
        verbose : bool, default=False
            Whether to print verbose output.
        """
        pass


class TestCommandDecorator(unittest.TestCase):
    def test_arguments(self):
        expected = {
            "start": {
                "name": "start",
                "help": "Starts the specified server.",
                "arguments": [
                    {
                        "name": "server",
                        "help": "The name of the server to start.",
                        "cls": str,
                        "default": clap.utils.MISSING,
                        "range": clap.metadata.Range(1, 1),
                    },
                ],
                "options": {},
                "short_option_map": {},
            },
        }

        t = Test()
        for command in t.commands.values():
            test_command(command, expected[command.name])
