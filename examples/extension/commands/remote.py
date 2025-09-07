from typing import Annotated

import clap


class Remote(clap.Extension):
    @clap.group(invoke_without_subcommand=True)
    def remote(self, *, verbose: Annotated[bool, clap.Short] = False) -> None:
        print("Invoked without a subcommand!")
        pass

    @remote.subcommand()
    def add(self, name: str, url: str) -> None:
        """Create a new remote.

        This command adds a remote named `name` for the repository at `url`.

        Parameters
        ----------
        name
            A unique identifier for the target remote.
        url
            A link to a git repository.
        """
        pass

    @remote.subcommand()
    def rename(self, old: str, new: str) -> None:
        """Change the name of a remote.

        This command will rename the remote named `old` to `new`.

        Parameters
        ----------
        old
            The current name of the target remote.
        new
            The new name for the target remote.
        """
        pass

    @remote.subcommand()
    def remove(self, name: str) -> None:
        """Delete a remote.

        This command removes the remote named `name`.

        Parameters
        ----------
        name
            The name of the remote to remove.
        """
        pass


def setup(app: clap.Application, /) -> None:
    app.add_extension(Remote(app))
