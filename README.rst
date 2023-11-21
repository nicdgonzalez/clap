CLAP
====

.. contents:: Table of Contents

Introduction
------------

|PyPI Version|

**CLAP** is the command-line argument parser that builds itself.

It is designed to be easy to use, by building itself based on function
signatures and documentation!

Getting Started
---------------

Requires Python 3.10+ and uses
`NumPy-style docstrings <https://github.com/numpy/numpydoc>`_.

* Available on PyPI as ``ndg.clap``. Install it with PIP.

.. code:: bash

    python -m pip install -U ndg.clap

Here is a quick example of how to construct a basic parser.

.. code:: python

    import clap


    class MyCommands(clap.Parser):
        """Represents a collection of commands that the user can execute."""

        def __init__(self) -> None:
            super().__init__(
                help="An example CLI tool created using CLAP.",
                epilog="Thank you for using CLAP!",
            )

        @clap.command()
        def greet(self, name: str, /, nervous: bool = False) -> None:
            """Print a greeting to the specified name.

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

The above example can be run as follows:

.. code:: console

    $ python example.py greet --help
    Prints a greeting to the specified name.

    USAGE: greet [OPTIONS] <NAME>

    OPTIONS:
      -h, --help   Display this help message and exit. [default: False]
      --nervous  Whether to greet the person nervously. [default: False]

    ARGUMENTS:
      name  The name of the person to greet. (required)

    $ python examples/basic.py greet "Gojo Satoru"
    Hello, Gojo Satoru!

    $ python examples/basic.py greet --nervous "Gojo Satoru"
    Um... hello, Gojo Satoru...

Additional examples can be found in the ``examples`` directory.


.. |PyPI Version| image:: https://badgen.net/pypi/v/ndg.clap
  :target: https://pypi.org/project/ndg.clap
