import logging
import sys

import clap

app = clap.Application(name="git")
log = logging.getLogger(__name__)

# This is a list of file stems containing an extension + `setup` function.
EXTENSIONS = ("remote", "submodule")


def main() -> None:
    for file_stem in EXTENSIONS:
        try:
            app.extend(name=f".{file_stem}", package="commands")
        except clap.errors.MissingSetupFunctionError as err:
            print(
                f"failed to load extension: {err}",
                file=sys.stderr,
            )
            sys.exit(1)

    _ = app.parse_args()


if __name__ == "__main__":
    main()
