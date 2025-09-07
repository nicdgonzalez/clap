"""
Parse numpydoc-style docstrings.
"""

import re
import textwrap
from typing import TypedDict


class Docstring(TypedDict, total=False):
    short_summary: str | None
    deprecation_warning: tuple[str, str] | None
    extended_summary: str | None
    parameters: dict[str, tuple[str, str]] | None
    returns: dict[str, str] | None
    yields: dict[str, tuple[str, str]] | None
    receives: dict[str, tuple[str, str]] | None
    other_parameters: dict[str, tuple[str, str]] | None
    raises: dict[str, str] | None
    warns: dict[str, str] | None
    warnings: str | None
    see_also: dict[str, str] | None
    notes: str | None
    references: dict[int, str] | None
    examples: str | None


def parse_doc(doc: str | None, /) -> Docstring:
    """Parse a numpydoc-style function docstring.

    This function automatically removes indentation, then splits the docstring
    into sections using double newlines as the delimiter. While the docstring
    itself is optional, if defined, the "Short Summary" section is required.
    The remaining sections are expected to appear in the order defined by the
    numpydoc documentation [here].

    [here]: https://numpydoc.readthedocs.io/en/latest/format.html#sections

    Parameters
    ----------
    doc : str | None
        The target function's docstring.

    Returns
    -------
    Docstring
        A dictionary containing section names (in snake_case) as keys,
        and their content broken up into easier-to-use Python objects.
    """
    # `None` indicates that the section was not present.
    result: Docstring = {
        "short_summary": None,
        "deprecation_warning": None,
        "extended_summary": None,
        "parameters": None,
        "returns": None,
        "yields": None,
        "receives": None,
        "other_parameters": None,
        "raises": None,
        "warns": None,
        "warnings": None,
        "see_also": None,
        "notes": None,
        "references": None,
        "examples": None,
    }

    if doc is None:
        return result

    sections = textwrap.dedent(doc).split("\n\n", maxsplit=-1)
    # `sections` always has at least one element, even if `docstring` is empty.
    result["short_summary"] = sections.pop(0).strip()

    try:
        next_section = sections[0]
    except IndexError:
        # There are no more sections.
        return result
    else:
        next_section = next_section.strip()

    # Check for the "Deprecation Warning" section.
    match = re.match(r"^\.\. deprecated:: ([\d\.]+)\n\s{4}(.*)", next_section)

    if match is not None:
        _ = sections.pop(0)
        version = match.group(1)
        message = re.sub(r"\s+", " ", match.group(2))
        result["deprecation_warning"] = (version, message)

        try:
            next_section = sections[0]
        except IndexError:
            # There are no more sections.
            return result
        else:
            next_section = next_section.strip()

    # Check for the "Extended Summary" section(s).
    if not is_section_with_heading(next_section):
        _ = sections.pop(0)
        chunks: list[str] = [next_section]

        while len(sections) > 0 and not is_section_with_heading(sections[0]):
            chunks.append(sections.pop(0))

        extended_summary = "\n\n".join(
            (re.sub(r"\s+", " ", chunk) for chunk in chunks)
        )
        result["extended_summary"] = extended_summary

    for section in sections:
        heading, _, content = section.split("\n", maxsplit=2)

        # As much as I would love a complete parser, not all fields are
        # required for our use-case; for now, handle only the necessary
        # sections.
        match heading.strip():
            case "Parameters":
                result["parameters"] = handle_parameters(content)
            case "Returns":
                pass
            case "Yields":
                pass
            case "Receives":
                pass
            case "Other Parameters":
                result["other_parameters"] = handle_parameters(content)
            case "Raises":
                pass
            case "Warns":
                pass
            case "Warnings":
                pass
            case "See Also":
                pass
            case "Notes":
                pass
            case "References":
                pass
            case "Examples":
                pass
            case _:
                pass

    return result


def is_section_with_heading(section: str, /) -> bool:
    sections = section.split("\n", maxsplit=1)

    if len(sections) < 2:
        # It definitely has no heading if it is only a single line.
        return False

    return sections[1].strip().startswith("---")


def handle_parameters(content: str, /) -> dict[str, tuple[str, str]]:
    matches = re.findall(
        r"^([\w_\d]+)(?:(?: : )([\w\d ,{}\"\'=]+))?$((?:\s{4,}.*\n?)+)",
        content,
        re.MULTILINE,
    )

    results: dict[str, tuple[str, str]] = {}

    for parameter, type_hint, summary in matches:
        summary = re.sub(r"\s+", " ", summary.strip())
        results[parameter] = (type_hint, summary)

    return results
