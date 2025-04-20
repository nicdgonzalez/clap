import dataclasses
import os
import textwrap
from typing import Protocol, runtime_checkable

from colorize import Colorize


class HelpFormatter:
    def __init__(
        self,
        width: int = 80,
        name_width: int = -1,
        indent: int = 2,
        placeholder: str = "[...]",
    ) -> None:
        try:
            terminal_size = os.get_terminal_size()
            columns = terminal_size.columns
        except OSError:
            columns = 80

        self.width = min(columns, width)
        self.name_width = name_width if name_width != -1 else self.width // 4
        self.indent = indent
        self.placeholder = placeholder

        # +2 for the spaces between `name` and `brief`.
        overhead = self.indent + len(self.placeholder) + 2

        if self.width < (full_name_length := self.name_width + overhead):
            raise ValueError(f"width must be greater than {full_name_length}")


@runtime_checkable
class SupportsRender(Protocol):
    def render(self, fmt: HelpFormatter) -> str:
        raise NotImplementedError


class Text(SupportsRender):
    def __init__(self, text: str, /) -> None:
        self.text = text

    def render(self, fmt: HelpFormatter) -> str:
        lines = textwrap.wrap(
            text=self.text,
            width=fmt.width,
            initial_indent="",
            subsequent_indent="",
            expand_tabs=True,
            tabsize=fmt.indent,
            replace_whitespace=True,
            fix_sentence_endings=False,
            break_long_words=True,
            break_on_hyphens=True,
            drop_whitespace=True,
            max_lines=None,
            placeholder="[...]",
        )
        return "\n".join(lines)


@dataclasses.dataclass
class Item:
    name: str
    brief: str


class Section(SupportsRender):
    def __init__(self, heading: str, /, *, skip_if_empty: bool = True) -> None:
        self.heading = heading
        self.skip_if_empty = skip_if_empty
        self.items: list[Item] = []

    def add_item(self, item: Item, /) -> "Section":
        self.items.append(item)
        return self

    def render(self, fmt: HelpFormatter) -> str:
        if self.skip_if_empty and len(self.items) < 1:
            return ""

        buffer = str(Colorize(f"{self.heading}:").underline().bold())
        buffer += "\n"

        indent = " " * fmt.indent
        longest_name = max((len(item.name) for item in self.items), default=0)
        name_width = min(longest_name, fmt.name_width)
        # +2 for the spaces between item name and brief.
        subsequent_indent = fmt.indent + name_width + 2

        items: list[str] = []

        for item in self.items:
            if len(item.name) > name_width:
                cut = name_width - len(fmt.placeholder)
                name = item.name[slice(0, cut, 1)] + fmt.placeholder

            name = str(Colorize(item.name.ljust(name_width, " ")).bold())

            lines = textwrap.wrap(
                # Avoid having to wrap due to punctuation.
                item.brief.rstrip("."),
                width=fmt.width - subsequent_indent,
                initial_indent="",
                subsequent_indent=" " * subsequent_indent,
                expand_tabs=True,
                tabsize=fmt.indent,
                replace_whitespace=True,
                fix_sentence_endings=False,
                break_long_words=True,
                break_on_hyphens=False,
                drop_whitespace=True,
                max_lines=2,
                placeholder="[...]",
            )
            brief = "\n".join(lines)
            items.append(f"{indent}{name}  {brief}")

        buffer += "\n".join(items)

        return buffer


@dataclasses.dataclass
class Arg:
    name: str
    required: bool | None


class Usage(SupportsRender):
    def __init__(self, program_name: str, /) -> None:
        self.program_name = program_name
        self.arguments: list[Arg] = []

    def add_argument(self, argument: Arg, /) -> "Usage":
        self.arguments.append(argument)
        return self

    def render(self, fmt: HelpFormatter) -> str:
        section = (
            Section("Usage", skip_if_empty=False).render(fmt=fmt).rstrip()
        )
        command = Colorize(self.program_name).bold()
        buffer = f"{section} {command}"

        for argument in self.arguments:
            match argument.required:
                case True:
                    buffer += f" <{argument.name}>"
                case False:
                    buffer += f" [{argument.name}]"
                case None:
                    buffer += f" {argument.name}"

        return buffer


class HelpMessage(SupportsRender):
    def __init__(self) -> None:
        self.root: list[SupportsRender] = []

    def add(self, child: SupportsRender, /) -> "HelpMessage":
        self.root.append(child)
        return self

    def render(self, fmt: HelpFormatter) -> str:
        rendered = [child.render(fmt=fmt) for child in self.root]
        result = filter(lambda r: r != "", rendered)
        return "\n\n".join(result)
