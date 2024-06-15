import sys

import clap

app = clap.Application(
    name="fuji",
    brief="A command-line application for managing Minecraft server",
)

extensions = [
    ".commands",
]


def main() -> int:
    for extension in extensions:
        app.extend(extension, package="fuji")

    app.parse_args()  # Defaults to `sys.argv`

    return 0


if __name__ == "__main__":
    sys.exit(main())
