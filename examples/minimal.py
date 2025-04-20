import clap


@clap.script()
def add(x: int, y: int) -> int:
    return x + y


if __name__ == "__main__":
    _ = add.run()
