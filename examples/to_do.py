#!/usr/bin/python3

from typing import Annotated

import clap

app = clap.Application(
    name="knight",
    brief="Automatically switch between system themes based on the time of day.",  # noqa: E501
    description=(
        """
🛡️ Knight allows you to switch system themes automatically based on the time of
day (for the GNOME desktop environment on Linux).

✨ Features

- Automatically toggle between light and dark theme.
- Determines sunrise and sunset times based on your location.
- Configurable through a dedicated configuration file.
- Supports changing themes manually, and pausing the automatic theme switcher.
        """
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
    hostname : str
        The address of the server to connect to.
    port : int
        A valid port number between 0 and 65535.
    silent : bool, default=False
        Whether to supress output.
    """
    raise NotImplementedError


@app.command()
def add(task: str) -> None:
    """Create a new task.

    Parameters
    ----------
    task : str
        A brief description for the task.
    """
    raise NotImplementedError


dummy_input = ["ping", "--silent", "--host=0.0.0.0", "-p", "25565"]
args = clap.parse(app, input=dummy_input)
print(args)
app.run(input=dummy_input)
