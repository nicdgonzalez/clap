"""
Basic
=====

This example demonstrates the basic usage of CLAP.

"""
import clap


class MyCommands(clap.Parser):
    """Represents the commands that are available to the user."""

    def __init__(self) -> None:
        super().__init__(
            help="This is an example CLI tool created using CLAP.",
            epilog="Thank you for using CLAP!",
        )

    @clap.command()
    def greet(self, name: str, /, nervous: bool = False) -> None:
        """Prints a greeting to the specified name.

        Parameters
        ----------
        name : str
            The name of the person to greet.
        nervous : bool, default=False
            Whether to greet the person nervously.
        """
        if nervous is True:
            print(f"Um... hello, {name}...")
        else:
            print(f"Hello, {name}!")


if __name__ == "__main__":
    parser = MyCommands()
    parser.parse()


"""
Output using [ndg.clap 0.1.0]:
-----------------------------------------------------------------------------
$ python examples/basic.py --help
This is an example CLI tool created using CLAP.

USAGE: basic.py <COMMAND> [OPTIONS] [ARGUMENTS]
For more information on a specific command, use '<COMMAND> --help'.

OPTIONS:
  -h, --help  Display this help message and exit. [default: False]

COMMANDS:
  greet  Prints a greeting to the specified name.

Thank you for using CLAP!

$ python examples/basic.py greet "Gojo Satoru"
$ python examples/basic.py greet --help
Prints a greeting to the specified name.

USAGE: greet [OPTIONS] <NAME>

OPTIONS:
  -h, --help   Display this help message and exit. [default: False]
  --nervous  Whether to greet the person nervously. [default: False]

ARGUMENTS:
  name  The name of the person to greet. (required)

Hello, Gojo Satoru!

$ python examples/basic.py greet --nervous "Gojo Satoru"
Um... hello, Gojo Satoru...
"""
