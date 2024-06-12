from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from builtins import dict as Dict
    from typing import Any

COMMAND_BRIEF_REGEX = re.compile(r"^(.*?)(?:\n\n|\Z)", re.DOTALL)
COMMAND_DESCRIPTION_REGEX = re.compile(
    r"^(?:.*?\n\n)?(.*?)(?:Parameters\n---+.*?)?(?:\n\n|\Z)", re.DOTALL
)
SECTION_REGEX_FMT = r"{name}\n-+\n\s*(.*?)(?:\n\n|\Z)"
PARAMETERS_SECTION_REGEX = re.compile(
    SECTION_REGEX_FMT.format(name="Parameters"), re.DOTALL
)
OTHER_PARAMETERS_SECTION_REGEX = re.compile(
    SECTION_REGEX_FMT.format(name="Parameters"), re.DOTALL
)
PARAMETER_DESCRIPTION_REGEX = re.compile(
    r"(?P<name>\S+)\s*:.*?\n(?P<description>.*?)(?=\S+\s*:|\Z)", re.DOTALL
)


class _Missing:
    __slots__ = ()

    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _Missing()


def fold_text(text: str, /) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_docstring(docstring: str, /) -> Dict[str, str]:
    result: Dict[str, str] = {}

    if (match := COMMAND_BRIEF_REGEX.search(docstring)) is not None:
        result["__brief__"] = fold_text(match.group(1))

    if (match := COMMAND_DESCRIPTION_REGEX.search(docstring)) is not None:
        result["__desc__"] = fold_text(match.group(1))

    result.update(**_get_parameter_descriptions(docstring))

    return result


def _get_parameter_descriptions(docstring: str, /) -> Dict[str, str]:
    sections = (PARAMETERS_SECTION_REGEX, OTHER_PARAMETERS_SECTION_REGEX)
    result: Dict[str, str] = {}

    for section in sections:
        if (match := section.search(docstring)) is None:
            continue

        # Imagine we have the following documentation on a function::
        #
        #   [...]
        #
        #   Parameters
        #   ----------
        #   arg1:
        #       A short description of `arg1`.
        #
        #   [...]
        #
        # `match.group(1)` starts from "arg1" and collects everything until
        # the next double newline (or end of string)
        matches = PARAMETER_DESCRIPTION_REGEX.findall(match.group(1))

        for param_name, param_desc in matches:
            result[param_name] = fold_text(param_desc)

    return result
