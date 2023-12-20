CLAP
====

.. contents:: Table of Contents

Introduction
------------

|PyPI Version|

**CLAP** is the command-line argument parser that builds itself.

It is designed to be easy to use, by building itself based on a function's
signature and documentation.

This project is not intended to be used for simple scripts, but rather
command-line tools that have multiple sub-commands and options. (I would like
to add support for simple scripts in the future.)

Getting Started
---------------

Requires Python 3.8+ and uses
`NumPy-style docstrings <https://github.com/numpy/numpydoc>`_.

* Available on PyPI as ``ndg.clap``. Install it with PIP.

.. code:: bash

    python -m pip install -U ndg.clap

For an example project, see `fuji <https://github.com/nicdgonzalez/fuji>`_.

Room for Improvement
--------------------

* Add support for simple scripts
* Add documentation using Sphinx
* Add unit tests
* Add examples
* Write a better README


.. |PyPI Version| image:: https://badgen.net/pypi/v/ndg.clap
  :target: https://pypi.org/project/ndg.clap
