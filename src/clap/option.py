class Option:
    """Represents a command-line flag (e.g., `--verbose`)"""

    def __init__(self, name: str, cls: type, brief: str) -> None:
        self.name = name
        self.cls = cls
        self.brief = brief
