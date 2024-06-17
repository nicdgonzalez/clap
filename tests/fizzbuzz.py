#!/usr/bin/python

from typing import Any, Annotated

import clap

script = clap.Script(brief="A simple demo of clap.Script!")


@script.main()
def fizzbuzz(
    min: int = 1,
    max: int = 100,
    *,  # keyword-only arguments are converted into options
    skip_empty: Annotated[bool, clap.Alias("s")] = False,
) -> Any:
    raise NotImplementedError


if __name__ == "__main__":
    _ = script.parse_args()  # defaults to sys.argv
