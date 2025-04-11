"""
Building a to-do app to demonstrate how to use `clap.Application` to build
a command-line interface that can perform different tasks.
"""

from typing import Annotated, Literal

import clap

app = clap.Application(
    brief="A simple command-line to-do app to demonstrate clap!",
    after_help="Additional examples can be found in the `examples` directory.",
)


@app.subcommand()
def new(*, task: str, priority: Literal["low", "medium", "high"]) -> None:
    """Create a new task.

    Parameters
    ----------
    task
        A brief summary explaining the task.
    priority
        Indicates how important the task is.
    """
    raise NotImplementedError


@app.subcommand()
def delete(id_: Annotated[int, clap.Rename("id")]) -> None:
    """Remove an existing task.

    Parameters
    ----------
    id_
        The id of the task to delete (shown by the `list` command).
    """
    raise NotImplementedError


@app.subcommand(name="list")
def list_(*, sort: bool = False) -> None:
    """Display all tasks.

    Parameters
    ----------
    sort
        Whether to order tasks by priority.
    """
    raise NotImplementedError


if __name__ == "__main__":
    app.run()
