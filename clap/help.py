"""
Help
====

A collection of functions and classes for generating the help message.

"""
from __future__ import annotations

import textwrap
from typing import NamedTuple, Protocol

__all__ = [
    "HelpFormatter",
]


class HelpItem(NamedTuple):
    """Represents an item in the help message."""

    name: str
    help: str


class HasHelpItemFormat(Protocol):
    """A protocol for objects that can be formatted as a `HelpItem`."""

    def help_item_format(self) -> HelpItem:
        ...


class HelpFormatter:
    """A class for formatting help messages.

    Parameters
    ----------
    width : int, optional
        The maximum width of the help message.
    name_width : int, optional
        The width of the name column.
    indent : int, optional
        The number of spaces to indent each item under a header.
    compact : bool, optional
        Whether to omit newlines between sections.
    """

    def __init__(
        self,
        width: int = 80,
        name_width: int = 20,
        indent: int = 2,
        compact: bool = False,
    ) -> None:
        if width < 50:
            raise ValueError(f"width must be at least 50, got {width}")
        self.width = width
        self.name_width = name_width
        self.indent = indent
        self.compact = compact


class HelpBuilder:
    """Represents the help message for a command-line interface."""

    def __init__(
        self,
        formatter: HelpFormatter = HelpFormatter(),
    ) -> None:
        """A builder class for generating the help message text.

        Parameters
        ----------
        width : int, optional
            The maximum width of the help message.
        name_width : int, optional
            The width of the name column.
        indent : int, optional
            The number of spaces to indent each item under a header.
        compact : bool, optional
            Whether to omit newlines between sections.
        """
        self.fmt = formatter
        self._text = ""
        self._buffer: list[HelpItem] = []
        self._placeholder: str | None = None  # see `placeholder` property

    @property
    def placeholder(self) -> str | None:
        """Text to display when there are no items in a section
        (e.g. "No commands available." or "No options available.").
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str | None) -> None:
        self._placeholder = value

    def build(self) -> str:
        """Builds the help message."""
        self.flush_buffer()
        return self._text

    def add_header(self, header: str, description: str = "") -> None:
        """Add a new section to the help message.

        Parameters
        ----------
        header : str
            The name of the section.
        description : str, optional
            A brief description of the section.
        """
        self.flush_buffer()
        if not self.fmt.compact:
            self.add_newline()
        _description = textwrap.wrap(
            description,
            # -2 for the colon and space
            width=self.fmt.width - len(header) - 2,
            max_lines=1,
        )
        description = _description.pop(0) if _description else description
        self.add_line(f"{header}: {description}")

    def add_item(self, item: HasHelpItemFormat) -> None:
        """Add an item to the help message.

        Parameters
        ----------
        item : HasHelpItemFormat
            The item to add.
        """
        self._buffer.append(item.help_item_format())

    def add_line(self, line: str) -> None:
        """Add a line to the help message.

        Parameters
        ----------
        line : str
            The line to add.
        """
        self._text += line + "\n"

    def add_newline(self, force: bool = False) -> None:
        """Add a newline to the help message."""
        self.add_line("") if force or not self.fmt.compact else None

    def flush_buffer(self) -> None:
        """Writes all of the items in the buffer to the help message. This is
        typically called automatically when a new section is being added or
        the message is being built.
        """
        indent = " " * self.fmt.indent
        if len(self._buffer) < 1:
            if self.placeholder is not None:
                self.add_line(f"{indent}{self.placeholder}")
            return
        # Perform calculations with static values outside of the while loop
        # to avoid needlessly repeating operations on each iteration.
        longest_name = max(len(name) for name, _ in self._buffer)
        # +2 for the two spaces between the name and description
        subsequent_indent = " " * (self.fmt.indent + longest_name + 2)
        width = self.fmt.width - self.fmt.indent - longest_name - 2
        while len(self._buffer) > 0:
            item = self._buffer.pop(0)
            description = "\n".join(
                textwrap.wrap(
                    item.help,
                    width=width,
                    subsequent_indent=subsequent_indent,
                    max_lines=2,
                )
            )
            self.add_line(
                f"{indent}{item.name.ljust(longest_name)}  {description}"
            )
