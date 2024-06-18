from .abc import *
from .annotations import *
from .arguments import *
from .commands import *
from .core import *
from .help import *

__version__ = "0.2.0"

# TODO:
# - Documentation:
#   - Make sure everything follows numpydoc style
#   - Document all modules, classes, functions
#   - Generate Sphinx documentation
# - Converter:
#   - converting unions/literals are not implemented
# - Parser:
#   - Range currently does nothing (I think), we only ever consume at most
#     one extra token at a time... (I assume this would require rewriting the
#     parser logic...)
#   - Requires/Conflicts are currently not implemented...
