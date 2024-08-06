from __future__ import annotations

import copy
import dataclasses
import os
import re
import textwrap
from typing import TYPE_CHECKING, NamedTuple, NewType, TypedDict

if TYPE_CHECKING:
    from typing import Any, Iterator, Optional

    from typing_extensions import Self

HelpInfo = TypedDict("HelpInfo", {"name": str, "brief": str})


class SectionItem(NamedTuple):
    name: str
    brief: str = ""


SectionMarker = NewType("SectionMarker", str)


@dataclasses.dataclass
class Section:
    name: str
    brief: str = ""
    children: list[SectionItem] = dataclasses.field(default_factory=list)
    placeholder: Optional[str] = None
    skip_if_empty: bool = False

    @property
    def marker(self) -> SectionMarker:
        return SectionMarker("__{}_MARKER__".format(self.name.upper()))

    def __iter__(self) -> Iterator[SectionItem]:
        return self.children.__iter__()

    def add_item(self, *, name: str, brief: str = "") -> None:
        self.children.append(SectionItem(name=name, brief=brief))


@dataclasses.dataclass
class TreeData:
    data: dict[str, Section] = dataclasses.field(default_factory=dict)
    message: str = ""

    def __iter__(self) -> Iterator[Section]:
        return self.data.values().__iter__()

    def add_line(self, line: str, /) -> None:
        self.message += "{}\n".format(line)

    def add_newline(self) -> None:
        self.message += "\n"


@dataclasses.dataclass
class HelpFormatter:
    width: int = 80
    name_width: int = -1
    indent: int = 2
    placeholder: str = "[...]"
    compact: bool = False

    def __post_init__(self) -> None:
        try:
            self.width = min(os.get_terminal_size().columns, 80)
        except OSError:
            self.width = 80

        if self.name_width < 0:
            self.name_width = self.width // 4

        # +2 for the double whitespace between `name` and `brief`
        overhead = self.indent + len(self.placeholder) + 2

        if self.width < (corrected := self.name_width + overhead):
            # if we don't throw our own error here, textwrap will throw
            # a vague error regarding placeholder text later on
            error = (
                "width must be greater than or equal to {} "
                "(name_width + indent + len(placeholder) + 2)"
            )
            raise ValueError(error.format(corrected))


class HelpBuilder:

    def __init__(
        self,
        formatter: HelpFormatter = HelpFormatter(),
        tree: TreeData = TreeData(),
    ) -> None:
        self._fmt = formatter
        self._tree = tree
        self._default_indent = " " * self._fmt.indent
        self._indent = self._default_indent

    @property
    def default_indent(self) -> str:
        return self._default_indent

    @property
    def indent(self) -> str:
        return self._indent

    @indent.setter
    def indent(self, value: str, /) -> None:
        self._indent = value

    def build(self) -> str:
        message_map: dict[str, str] = {}

        for section in self._tree:
            message = self._format_section(section)

            if not message:
                # remove the marker from the message if the section is empty.
                # if we don't do this, the message will have a trailing newline
                # for every skipped section
                m = self._tree.message.replace(
                    "%({})s".format(section.marker), ""
                )
                self._tree.message = m
                continue

            message_map[section.marker] = message

        return re.sub("\n{3,}", "\n\n", self._tree.message % message_map)

    def add_section(
        self,
        name: str,
        *,
        brief: str = "",
        placeholder: Optional[str] = None,
        skip_if_empty: bool = False,
    ) -> Self:
        section = Section(
            name=name,
            brief=brief,
            placeholder=placeholder,
            skip_if_empty=skip_if_empty,
        )
        self._tree.data[name] = copy.deepcopy(section)

        # `self._tree.add_line()` is not used here because it would add
        # a newline to the marker, which after expansion already has a newline
        self._tree.message += "%({})s".format(section.marker)

        if not self._fmt.compact:
            self._tree.add_newline()

        return self

    def get_section(self, name: str, /) -> Optional[Section]:
        return self._tree.data.get(name)

    def add_line(self, line: str, **params: Any) -> Self:
        wrapped = textwrap.wrap(
            line,
            width=params.pop("width", self._fmt.width),
            initial_indent=params.pop("initial_indent", ""),
            subsequent_indent=params.pop(
                "subsequent_indent", self._default_indent
            ),
            placeholder=params.pop("placeholder", self._fmt.placeholder),
            max_lines=params.pop("max_lines", 2),
            **params,
        )
        message = "\n".join(wrapped)
        self._tree.add_line(message)

        if not self._fmt.compact:
            self._tree.add_newline()

        return self

    def add_newline(self, /, force: bool = False) -> Self:
        if not self._fmt.compact or force:
            self._tree.add_newline()

        return self

    def _format_section(self, section: Section, /) -> str:
        if not section.children and section.skip_if_empty:
            return ""

        message = self._create_section_header(section)

        if not section.children:
            if section.placeholder is not None:
                message += "{}{}\n".format(
                    self.default_indent, section.placeholder
                )

            return message

        # prepare the arguments that will be passed to `self._format_item()`

        longest = max((len(c.name) for c in section.children), default=0)
        name_width = min(longest, self._fmt.name_width)
        indent_width = self._fmt.indent + name_width
        max_lines: Optional[int] = 2

        # if there is no name or no brief, treat it as if it is a paragraph
        # and remove the max lines limit
        for child in section.children:
            if not child.name or not child.brief:
                max_lines = None
                break
            else:
                continue
        else:
            # +2 for the double whitespace separator between name and brief
            indent_width += 2

        subsequent_indent = " " * indent_width

        for child in section.children:
            message += self._format_item(
                child,
                name_width=name_width,
                subsequent_indent=subsequent_indent,
                max_lines=max_lines,
            )

        return message

    def _create_section_header(self, section: Section, /) -> str:
        message = "{}:".format(section.name)

        if section.brief:
            message += " {}".format(section.brief)

        message += "\n"

        return message

    def _format_item(
        self, item: SectionItem, *, name_width: int, **params: Any
    ) -> str:
        name = item.name.ljust(name_width)
        placeholder = params.get("placeholder", self._fmt.placeholder)
        cut = name_width - len(placeholder)

        if len(name) > name_width:
            name = name[:cut] + placeholder

        text = "{}  {}".format(name, item.brief).strip()

        wrapped = textwrap.wrap(
            text,
            width=self._fmt.width,
            initial_indent=self.indent,
            subsequent_indent=params.pop("subsequent_indent", self.indent),
            placeholder=params.pop("placeholder", self._fmt.placeholder),
            max_lines=params.pop("max_lines", 2),
            **params,
        )

        return "{}\n".format("\n".join(wrapped))
