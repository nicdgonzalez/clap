import sys
from typing import Annotated

import clap


class Parser(clap.ArgumentParser):
    min: Annotated[int, clap.Long, clap.Short("n")] = 1
    max: Annotated[int, clap.Long, clap.Short("x")] = 100


def main() -> None:
    args: Parser = Parser.try_parse(
        sys.argv[1:] if len(sys.argv) > 1 else ["--min", "1", "--max", "100"]
    )

    if args.min < args.max:
        start, stop = args.min, args.max
    else:
        start, stop = args.max, args.min

    stop += 1  # If the user set max to 100, it should stop at 100

    mapping = {
        3: "fizz",
        5: "buzz",
    }

    buffer = ""

    for i in range(start, stop):
        for n, value in mapping.items():
            if i % n == 0:
                buffer += value

        print(f"{i}: {buffer}")
        buffer = ""


if __name__ == "__main__":
    main()
