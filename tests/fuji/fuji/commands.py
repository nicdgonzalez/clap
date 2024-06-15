from typing_extensions import Annotated

import clap


class FujiCommands(clap.Extension):

    def __init__(self, app: clap.Application, /) -> None:
        self.app = app

    @clap.command()
    def setup(self, directory: str) -> None:
        """Create the necessary files for Fuji to operate.

        Parameters
        ----------
        directory:
            The location to store all of Fuji's data files.
        """
        raise NotImplementedError

    @clap.command()
    def list(self) -> None:
        """Display all of the available Minecraft servers."""
        raise NotImplementedError

    @clap.command()
    def new(
        self,
        name: str,
        *,
        accept_eula: Annotated[bool, clap.Alias("y")] = False,
    ) -> None:
        """Creates a new Minecraft server.

        Parameters
        ----------
        name: str
            A unique name for the server.
        accept_eula: bool
            Set `eula=true` without prompting for user input.
        """
        raise NotImplementedError

    @clap.command()
    def start(self, name: str) -> None:
        """Starts the specified Minecraft server."""
        raise NotImplementedError

    @clap.command()
    def stop(self, name: str) -> None:
        """Stops the specified Minecraft server."""
        raise NotImplementedError


def setup(app: clap.Application) -> None:
    app.add_extension(FujiCommands(app))
