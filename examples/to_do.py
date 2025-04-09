#!/usr/bin/python3

from typing import Annotated

import clap

app = clap.Application(
    name="knight",
    brief="Clone a repository into a new directory.",
    description=(
        """Clones a repository into a newly created directory, creates
remote-tracking branches for each branch in the cloned repository (visible
using git branch --remotes), and creates and checks out an initial branch
that is forked from the cloned repository’s currently active branch."""
    ),
    after_help="Repository: https://github.com/nicdgonzalez/knight",
)


@app.command()
def ping(
    *,
    host: str,
    port: Annotated[int, clap.Short],
    silent: Annotated[bool, clap.Short] = False,
) -> None:
    """Check the status of the target server.

    Parameters
    ----------
    host : str
        The address of the server to connect to.
    port : int
        A valid port number between 0 and 65535.
    silent : bool, default=False
        Whether to supress output.
    """
    print("Pinging server...")


@app.command()
def add(task: str) -> None:
    """Create a new task.

    Parameters
    ----------
    task : str
        A brief description for the task.
    """
    raise NotImplementedError


@app.command()
def remove(task: str) -> None:
    """Delete an existing task.

    Parameters
    ----------
    task : str
        A brief description for the task.
    """
    raise NotImplementedError


app.run()
