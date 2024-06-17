# Command-line Argument Parser

<a name="introduction"></a>
## Introduction

[![pypi-version](https://badgen.net/pypi/v/ndg.clap)](https://pypi.org/project/ndg.clap)

**ndg.clap** is the command-line argument parser that builds itself.

It is designed to be easy to use by generating all of the boilerplate code
based on function signatures and documentation (things you should already be
adding to your code anyway).

This project is missing a lot of features that you would otherwise get from
the built-in `argparse` library, though I plan to add everything in eventually.

[Introduction](#introduction) | [Installation](#installation) | [Quickstart](#quickstart)

<a name="installation"></a>
## Installation

**Python 3.9 or higher is required.**

To install the library, run the following command:

```bash
python -m pip install ndg.clap
```

<a name="quickstart"></a>
## Quickstart

> [!NOTE]
> This library currently only supports parsing through
> [NumPy-style docstrings](https://github.com/numpy/numpydoc).

### Script

See the [examples/fizzbuzz.py](./examples/fizzbuzz.py) for the code.

```console
$ python ./examples/fizzbuzz.py --help
A simple FizzBuzz implementation to demo `clap.Script`!

DESCRIPTION:
  FizzBuzz is a simple programming task where you iterate over a range of values
  and print either "Fizz" or "Buzz" when the index is divisible by `3` or `5`
  (respectively). If the index is divisible by both values, print both (i.e.
  "FizzBuzz").

USAGE:
  fizzbuzz.py [--help | --min | --max | --skip-empty]

OPTIONS:
  -h, --help        Shows this help message and exits
  --min             The index to start from [default: 1]
  --max             The index to stop at (inclusive) [default: 100]
  -s, --skip-empty  Whether to skip indexes that don't print anything
```

### Application

See the [examples/demo](./examples/demo) directory for the code of this simplified
example, or check out [Fuji](https://github.com/nicdgonzalez/fuji) for a full-fledged
project!

```console
$ cd ./examples/demo
$ python -m task_app --help
[WORK IN PROGRESS]
```
