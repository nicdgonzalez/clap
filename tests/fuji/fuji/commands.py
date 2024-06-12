import clap


class FujiCommands(clap.Extension):

    def __init__(self, app: clap.Application, /) -> None:
        self.app = app

    @clap.Command.from_function
    def setup(self, directory: str) -> None:
        """Initialize the Fuji project"""
        raise NotImplementedError

    @clap.Command.from_function
    def list(self) -> None:
        """Display all of the available servers"""
        raise NotImplementedError

    @clap.Command.from_function
    def new(self, name: str, *, accept_eula: bool = False) -> None:
        raise NotImplementedError

    @clap.Command.from_function
    def start(self, name: str) -> None:
        raise NotImplementedError

    @clap.Command.from_function
    def stop(self, name: str) -> None:
        raise NotImplementedError


def setup(app: clap.Application) -> None:
    app.add_extension(FujiCommands(app))
