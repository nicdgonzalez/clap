import clap


class FujiCommands(clap.Extension):

    def __init__(self, app: clap.Application, /) -> None:
        self.app = app

    @clap.command()
    def setup(self, directory: str) -> None:
        """Create the necessary files for Fuji to operate.

        It does this by blah blah blah...

        Parameters
        ----------
        directory:
            The location to store all of Fuji's data files.
        """
        raise NotImplementedError

    @clap.command()
    def list(self) -> None:
        """Display all of the available Minecraft servers"""
        raise NotImplementedError

    @clap.command()
    def new(self, name: str, *, accept_eula: bool = False) -> None:
        """Create a new Minecraft server"""
        raise NotImplementedError

    @clap.command()
    def start(self, name: str) -> None:
        """Start the specified Minecraft server"""
        raise NotImplementedError

    @clap.command()
    def stop(self, name: str) -> None:
        """Stop the specified Minecraft server"""
        raise NotImplementedError


def setup(app: clap.Application) -> None:
    app.add_extension(FujiCommands(app))
