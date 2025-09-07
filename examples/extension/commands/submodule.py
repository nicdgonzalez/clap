import pathlib
from typing import Annotated

import clap


class Submodule(clap.Extension):
    # TODO: This should print the usage message since
    # `invoke_without_subcommand` is `False`.
    @clap.group(invoke_without_subcommand=False)
    def submodule(self, *, quiet: bool = False, cached: bool = False) -> None:
        pass

    @submodule.subcommand()
    def add(
        self,
        repository: str,
        *,
        branch: Annotated[str, clap.Short],
        force: Annotated[bool, clap.Short],
        name: str,
    ) -> None:
        pass

    # TODO: Variable length positional arguments are currently not supported.
    # @submodule.subcommand()
    # def status(self, *path: pathlib.Path, cached: bool) -> None:
    #     pass

    @submodule.subcommand()
    def init(self, path: pathlib.Path | None = None) -> None:
        pass


def setup(app: clap.Application, /) -> None:
    app.add_extension(Submodule(app))
