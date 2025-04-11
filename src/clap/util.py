def kebab_case(s: str, /) -> str:
    return s.replace("_", "-")


def snake_case(s: str, /) -> str:
    return s.replace("-", "_")
