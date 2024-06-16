# Command-line Argument Parser

<a name="introduction"></a>
## Introduction

[![pypi-version](https://badgen.net/pypi/v/ndg.clap)](https://pypi.org/project/ndg.clap)

**ndg.clap** is the command-line argument parser that builds itself.

It is designed to be easy to use by generating most of the boilerplate code
based on function signatures and documentation (stuff you should already be
adding to your code anyway).

This is a passion project. It is missing a lot of features that you would
otherwise get from the built-in `argparse` library, but I plan to add
everything in on an as-need basis.

[Introduction](#introduction) | [Quickstart](#quickstart) | [Getting Started](#getting-started)

<a name="quickstart"></a>
## Quickstart

Requires Python 3.9+ and uses
[NumpPy-style docstrings](https://github.com/numpy/numpydoc)

* Available on PyPI as `ndg.clap`. You can install it using PIP:

```bash
python -m pip install ndg.clap
```

For an example project, see [Fuji](https://github.com/nicdgonzalez/fuji).

<a name="getting-started"></a>
## Getting Started

ndg.clap has (2) interfaces: **Application** and **Script**. For this demo,
we'll be using Script to wrap a single global function and then call it from
the command line. (If you want to be able to choose from multiple
functions/methods, you would use Application instead.)

* Start by importing *clap* and instantiating a new `clap.Script` object.

```python
import clap

script = clap.Script(brief="A simple demo of clap.Script!")
```

* To mark the *main* function of the script, use the `@script.main()`
decorator. The result of the main function will be retrievable at the
end, so return whatever you'd like!

```python
@script.main()
def fizzbuzz(...) -> None:
    raise NotImplementedError
```

* Python 3.9 added a new type to the *typing* module,
[`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated).
This allows you to add metadata to the parameters in a function's signature.
Among other things, you can use this to create short options for long options
(e.g. `-h` for `--help`, `-V` for `--version`, etc).

```python
from typing import Annotated
...
@script.main()
def fizzbuzz(
    # positional arguments are converted into positionals
    min: int = 1,
    max: int = 100,
    *,
    # keyword-only arguments are converted into options
    skip_empty: Annotated[bool, clap.Alias("s")] = False,
) -> None:
    raise NotImplementedError
```

* If we add the following to the bottom of the file,

```python
if __name__ == "__main__":
    _ = script.parse_args()  # defaults to sys.argv
```

* and pass `--help` to the script, we might get something like:

```console
$ python fizzbuzz.py --help
A simple demo of clap.Script!

USAGE:
  fizzbuzz.py [--help | --skip-empty] [min] [max]

OPTIONS:
  -h, --help        Shows this help message and exits
  -s, --skip-empty

ARGUMENTS:
  min   [default: 1]
  max   [default: 100]
```

WORK IN PROGRESS......
