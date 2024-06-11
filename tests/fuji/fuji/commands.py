import clap


class FujiCommands(clap.Extension):

    def __init__(self, app: clap.Application, /) -> None:
        self.app = app

    @clap.Command
    def setup(self, directory: str) -> None:
        raise NotImplementedError

    @clap.Command
    def list(self) -> None:
        raise NotImplementedError

    @clap.Command
    def new(self, name: str, *, accept_eula: bool = False) -> None:
        raise NotImplementedError

    @clap.Command
    def start(self, name: str) -> None:
        raise NotImplementedError

    @clap.Command
    def stop(self, name: str) -> None:
        raise NotImplementedError


def setup(app: clap.Application) -> None:
    app.add_extension(FujiCommands(app))
