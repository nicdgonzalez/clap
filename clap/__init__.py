"""
CLAP
====

Command Line Argument Parser (CLAP) is a library for parsing command-line
arguments.

Examples
--------
>>> from typing import Annotated
>>>
>>> import clap
>>> from clap.metadata import Short, Conflicts
>>>
>>> @clap.command(name="start")
... def start(
...     server: str,
...     /,
...     *,
...     verbose: Annotated[bool, Short('v'), Conflicts("quiet")] = False,
...     quiet: Annotated[bool, Short('q')] = False,
... ) -> None:
...     \"\"\"Starts the specified server.
...
...     Parameters
...     ----------
...     server : str
...         The name of the server to start.
...     verbose : bool, default=False
...         Whether to print verbose output.
...     quiet : bool, default=False
...         Whether to suppress all output.
...     \"\"\"
...     ...

"""

__version__ = "0.1.2"

from .arguments import *
from .commands import *
from .help import *
from .metadata import *
from .parser import *
