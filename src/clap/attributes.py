class Short(str):
    def __new__(cls, o: object) -> "Short":
        c = super().__new__(cls, o)

        if len(c) != 1:
            raise ValueError("expected short to be a single character")
        elif not c.isalpha():
            raise ValueError("expected short to be a letter")

        return c
