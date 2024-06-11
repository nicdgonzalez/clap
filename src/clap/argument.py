class Argument:
    """Represents a positional-only command-line argument"""

    def __init__(self, name: str, cls: type, brief: str) -> None:
        self.name = name
        self.cls = cls
        self.brief = brief
