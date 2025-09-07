import pathlib
from typing import Annotated

import clap

app = clap.Application(
    name="toolbox",
    brief="A collection of utilities and tools to make development easier.",
    after_help="Built with love using clap!",
)


class Http(clap.Extension):
    def __init__(self, app: clap.Application, /) -> None:
        self.app = app

    @clap.group()
    def http() -> None:
        """A collection of HTTP-related commands."""

    @http.subcommand()
    def ping(
        *,
        address: Annotated[str, clap.Short],
        port: Annotated[int, clap.Short],
    ) -> None:
        """Check whether the target `address` is currently available.

        Parameters
        ----------
        address
            The hostname to connect to.
        port
            The target port number (between 0 and 65535).
        """


class Python(clap.Extension):
    def __init__(self, app: clap.Application, /) -> None:
        self.app = app

    @clap.group()
    def py() -> None:
        """A collection of Python-related commands."""

    @py.subcommand()
    def test() -> None:
        """Run tests."""

    @py.subcommand()
    def install(package: str, *, git: str, path: pathlib.Path) -> None:
        """Add an external dependency to the project.

        Parameters
        ----------
        package
            The name of the package to install.
        git
            The URL to a git repository to install from.
        path
            The path to a package stored on the same machine.
        """

    @py.subcommand()
    def type_check(*, strict: bool) -> None:
        """Run a static type checker over the source code.

        Parameters
        ----------
        strict
            Whether to enable strict type checking.
        """


# If these extensions were stored in separate files:
#
# file: extensions/http.py
#
# ...
#
# def setup(app: clap.Application, /) -> None:
#     app.add_extension(Http(app))
#
# Then in the file where `app` is defined:
# app.extend("http", package="extensions")
#
# Since they are in the same file here, we can just add them directly:
app.add_extension(Http(app))
app.add_extension(Python(app))


if __name__ == "__main__":
    app.parse_args()
