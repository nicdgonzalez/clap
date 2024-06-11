class Short:
    def __init__(self, __c: str, /) -> None:
        if len(__c) != 1:
            raise ValueError("expected short to be a single character")

        self.inner = __c
