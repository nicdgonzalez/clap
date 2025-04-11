import clap


@clap.script()
def add(x: int, y: int) -> None:
    return x + y


add.run()
