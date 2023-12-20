"""
Help
====

This module implements the help-related functionality of the command-line
interface.

"""
from __future__ import annotations

import copy
import dataclasses
import os
import textwrap
from typing import TYPE_CHECKING, Mapping, NamedTuple, NewType, Protocol

if TYPE_CHECKING:
    from builtins import dict as Dict
    from builtins import list as List
    from typing import Any, Optional


class CanDisplayHelp(Protocol):
    """A protocol that represents an object that can display a help message.

    The following objects implement this protocol:

    - :class:`Command`
    - :class:`Group`
    - :class:`Parser`

    Methods
    -------
    display_help(fmt: HelpFormatter)
        Display the help message for the object.
    """

    def display_help(self, *, fmt: HelpFormatter) -> None:
        ...


class HelpInfo(Mapping):
    name: str
    brief: str


@dataclasses.dataclass()
class HelpFormatter:
    """Represents the configuration for the help message.

    Attributes
    ----------
    width : int
        The maximum width of the help message. By default, the width is either
        80 or the width of the terminal, whichever is smaller.
    name_width : Optional[int]
        The maximum width of the names in the help message. By default, the
        width is 25% of :attr:`width`.
    indent : int
        The number of spaces to indent each item in a section.
    placeholder : str
        The placeholder to use if a line is too long. By default, the
        placeholder is ``[...]``.
    compact : bool
        Whether to omit newlines between sections.
    """

    width: int = min(os.get_terminal_size().columns, 80)
    name_width: int = -1
    indent: int = 2
    placeholder: str = "[...]"
    compact: bool = False

    def __post_init__(self) -> None:
        if self.name_width < 0:
            self.name_width = self.width // 4

        # In order to ensure that we have enough space to display the
        # placeholder, we need to ensure that the width is greater than or
        # equal to the following:
        # +2 for the double whitespace separator between name and brief
        overhead = self.indent + len(self.placeholder) + 2
        if self.width < (corrected := self.name_width + overhead):
            # If we don't throw an error here, textwrap will throw a
            # vague error regarding placeholder text later on.
            raise ValueError(
                f"width must be greater than or equal to {corrected} "
                "(name_width + indent + len(placeholder) + 2)"
            )


"""
For context, the help message is structured as a tree. The root node is the
"help" command itself, and the children of the root node are the different
sections of the help message. For example, a command's help message might have
the following structure::

    A brief description of the command.

    DESCRIPTION:
        lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        eiusmod tempor incididunt ut labore et dolore magna aliqua.

    USAGE:
        command [options] <arg1> <arg2>

    OPTIONS:
        -h, --help     Show this help message and exit.
        -v, --verbose  Display more information while running.
        -q, --quiet    Display no information while running.

    ARGUMENTS:
        arg1  The first argument.
        arg2  The second argument.

    Read the documentation for more information.

The root node would have the following children (in order):
      ^ (:class:`Help`)                   ^ (:class:`Node`)

    * "DESCRIPTION"
    * "USAGE"
    * "OPTIONS"
    * "ARGUMENTS"

Each of these children would have a brief description of the section, and
possibly children of their own. For example, the "OPTIONS" node might have the
following children:

    * ("-h, --help", "Show this help message and exit.")
    * ("-v, --verbose", "Display more information while running.")
    * ("-q, --quiet", "Display no information while running.")

Each of these children would have a brief description of the option.

The help message is built up by traversing the tree and printing out the
information in each node. The root node is not printed, but its children are
printed out in the order they were added to the root node.
"""


class Leaf(NamedTuple):
    """Represents a leaf node in the help tree."""

    name: Optional[str]
    brief: Optional[str]

    def __post_init__(self) -> None:
        if self.name is None and self.brief is None:
            raise ValueError("name and brief cannot both be None")


NodeMarker = NewType("NodeMarker", str)


@dataclasses.dataclass()
class Node:
    """Represents a node in the help tree.

    Attributes
    ----------
    name : :class:`str`
        The name of the node.
    brief : :class:`str`
        A brief description of the node.
    children : :class:`list`
        A list of children of this node.
    placeholder : :class:`str`
        The text to display when the node has no children.
    skip_if_empty : :class:`bool`
        Whether to omit from the help message if the node has no children.
    """

    name: str
    brief: Optional[str] = None
    children: List[Leaf] = dataclasses.field(default_factory=list)
    placeholder: Optional[str] = None
    skip_if_empty: bool = False

    @property
    def marker(self) -> NodeMarker:
        """A unique identifier for the node to use when formatting the help
        message.

        Examples
        --------
        The marker is placed in the help message to indicate where the node
        should be placed. For example, the marker for the "OPTIONS" node might
        look like this::

            %(__OPTION_MARKER__)s

        To ensure that all elements in a section are aligned properly, the
        nodes are deferred until the entire tree is built. To preserve order,
        a marker is placed in the help message where the node should be.

        Returns
        -------
        :class:`str`
            The marker for the node.
        """
        return NodeMarker(f"__{self.name.upper()}_MARKER__")

    def __iter__(self) -> Node:
        return self.children.__iter__()

    def add_item(
        self, /, *, name: Optional[str] = None, brief: Optional[str] = None
    ) -> None:
        self.children.append(Leaf(name=name, brief=brief))


class HelpTree:
    """Represents the help tree.

    The help tree is separated from the help message itself so that multiple
    help messages can be built from the same tree. This also allows for a tree
    to be the base of a new help message.

    Attributes
    ----------
    data : :class:`dict`
        A mapping of section names to :class:`Node` objects.
    message : :class:`str`
        The help message to display.
    """

    def __init__(self) -> None:
        self.data: Dict[str, Node] = {}
        self.message = ""

    def __iter__(self) -> Node:
        return self.data.values().__iter__()

    def add_line(self, line: str, /) -> None:
        """Write a line to the help message.

        Parameters
        ----------
        line : :class:`str`
            The line to write to the help message.
        """
        self.message += line + "\n"

    def add_newline(self) -> None:
        """Write a newline to the help message."""
        self.message += "\n"


class Help:
    def __init__(
        self,
        fmt: HelpFormatter = HelpFormatter(),
        tree: HelpTree = HelpTree(),
    ) -> None:
        self.fmt = fmt
        self.tree = copy.deepcopy(tree)

    @property
    def default_indent(self) -> str:
        """The default indentation to use for each item in a section.

        This can be passed as the ``initial_indent`` or ``subsequent_indent``
        parameter to :meth:`add_line`.

        Returns
        -------
        :class:`str`
            A string of spaces to use for indentation, based on the value of
            :attr:`fmt.indent`.
        """
        return " " * self.fmt.indent

    def copy_tree(self) -> HelpTree:
        """Create a deep copy of the help tree.

        This is useful if you want to build multiple help messages from the
        same tree.

        Returns
        -------
        :class:`HelpTree`
            A deep copy of the help tree.
        """
        return copy.deepcopy(self.tree)

    def build(self) -> str:
        """Generate the help message.

        This method traverses the help tree, expanding all of the nodes and
        formatting the help message based on the configuration provided via
        :attr:`fmt`.

        Returns
        -------
        :class:`str`
            The help message.
        """
        message_map: Dict[str, str] = {}

        for node in self.tree:
            message = self._format_node(node)

            if not message:
                # Remove the marker from the message if the node is empty.
                # If we don't do this, the message will have a trailing
                # newlines for every skipped node.
                m = self.tree.message.replace(f"%({node.marker})s\n", "")
                self.tree.message = m
                continue

            message_map[node.marker] = message

        return self.tree.message % message_map

    def add_section(
        self,
        name: str,
        /,
        *,
        brief: Optional[str] = None,
        placeholder: Optional[str] = None,
        skip_if_empty: bool = False,
    ) -> Node:
        """Create a new section in the help message.

        Parameters
        ----------
        name : :class:`str`
            The name of the section.
        brief : :class:`str`, optional
            A brief description of the section.
        placeholder : :class:`str`, optional
            The text to display when the section has no children.
        skip_if_empty : :class:`bool`, optional
            Whether to omit the section from the help message if it has no
            children.

        Returns
        -------
        :class:`Node`
            The node that represents the section. This can be used to add
            items to the section.
        """
        node = Node(
            name=name,
            brief=brief,
            placeholder=placeholder,
            skip_if_empty=skip_if_empty,
        )
        self.tree.data[name] = copy.deepcopy(node)

        # `add_line` is not used here because it would add a newline to the
        # marker, which, after expansion, already has a newline.
        self.tree.message += f"%({node.marker})s"

        if not self.fmt.compact:
            self.tree.message += "\n"

        return self.tree.data[name]

    def add_line(
        self,
        line: str,
        **params: Any,
    ) -> None:
        """Write a line to the help message.

        Parameters
        ----------
        line : :class:`str`
            The line to write to the help message.
        **params
            Additional parameters to pass to :func:`textwrap.wrap`.
        """
        wrapped = textwrap.wrap(
            line,
            width=params.pop("width", self.fmt.width),
            initial_indent=params.pop("initial_indent", ""),
            subsequent_indent=params.pop(
                "subsequent_indent", self.default_indent
            ),
            placeholder=params.pop("placeholder", self.fmt.placeholder),
            max_lines=params.pop("max_lines", 2),
            **params,
        )
        message = "\n".join(wrapped)
        self.tree.add_line(message)

    def add_newline(self, /, force: bool = False) -> None:
        """Write a newline to the help message.

        Parameters
        ----------
        force : :class:`bool`, optional
            Whether to force a newline, even if :attr:`fmt.compact` is
            ``True``.
        """
        if not self.fmt.compact or force:
            self.tree.add_newline()

    def _format_node(self, node: Node, /) -> str:
        if not node.children and node.skip_if_empty:
            return ""

        message = f"{node.name}:"

        if node.brief is not None:
            message += f" {node.brief}"

        message += "\n"

        if not node.children:
            if node.placeholder is not None:
                message += f"{self.default_indent}{node.placeholder}\n"

            return message

        longest_name = max(
            (len(c.name) for c in node.children if c.name), default=0
        )
        name_width = min(longest_name, self.fmt.name_width)
        indent_width = self.fmt.indent + name_width
        max_lines = 2

        for child in node.children:
            if child.name is None or child.brief is None:
                max_lines = None
                break
        else:
            # +2 for the double whitespace separator between name and brief
            indent_width += 2

        subsequent_indent = " " * indent_width

        for child in node.children:
            message += self._format_child(
                child,
                name_width=name_width,
                subsequent_indent=subsequent_indent,
                max_lines=max_lines,
            )

        return message

    def _format_child(
        self,
        child: Leaf,
        /,
        *,
        name_width: int,
        **params: Any,
    ) -> str:
        name = (child.name or "").ljust(name_width)
        brief = child.brief or ""

        cutoff = name_width - len(self.fmt.placeholder)
        if len(name) > name_width:
            name = name[:cutoff] + self.fmt.placeholder

        wrapped = textwrap.wrap(
            f"{name}  {brief}" if name and brief else (name or brief),
            width=self.fmt.width,
            initial_indent=self.default_indent,
            subsequent_indent=params.pop(
                "subsequent_indent", self.default_indent
            ),
            placeholder=self.fmt.placeholder,
            max_lines=params.pop("max_lines", 2),
        )

        return "\n".join(wrapped) + "\n"
