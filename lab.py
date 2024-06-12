import inspect
import json
import sys

import clap
import clap.options
from clap.utils import parse_docstring
from tests.fuji.fuji import commands

app = clap.Application()
fuji = commands.FujiCommands(app)
for command in fuji.commands:
    print(command.name, command.brief)
# command = fuji.setup
# command.callback.__self__ = fuji
# command("~/.fuji")


def start_server(world_name: str, port: int = 6969) -> None:
    """Starts the server

    some long description about what the start_server command does.

    Parameters
    ----------
    world_name:
        The name of the world you want to open
    port:
        the port to open the server on
    """
    print("Starting server")


docstring = inspect.getdoc(start_server)
if docstring is None:
    print("function does not have a docstring")
    sys.exit(1)

print(json.dumps(parse_docstring(docstring), indent=4))
