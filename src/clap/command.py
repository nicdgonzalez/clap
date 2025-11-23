import dataclasses
import inspect
from typing import Annotated, Any, Self, get_args, get_origin

from .argument import Argument
from .metadata import Help, Long, Short
from .option import Option
from .sentinel import MISSING


class Subcommand:
    subcommands: dict[str, type["Command"]]

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if not hasattr(cls, "subcommands"):
            annotations = inspect.get_annotations(cls)
            subcommands: dict[str, type[Command]] = {}

            for name, tp in annotations.items():
                if not issubclass(tp, Command):
                    continue

                subcommands[name] = tp

            cls.subcommands = subcommands

        return super().__new__(cls)


@dataclasses.dataclass
class Schema:
    subcommand: tuple[str, type[Subcommand]] | None = None
    arguments: list[Argument[Any]] = dataclasses.field(default_factory=list)
    options: dict[str, Option[Any]] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_annotations(cls, annotations: dict[str, Any], /) -> Self:
        subcommand: tuple[str, type[Subcommand]] | None = None
        arguments: list[Argument[Any]] = []
        options: dict[str, Option[Any]] = {}

        for name, tp in annotations.items():
            argument_type: type[Any] = tp
            metadata: tuple[Any, ...] = ()

            if get_origin(tp) is Annotated:
                argument_type, *metadata = get_args(tp)

            if issubclass(argument_type, Subcommand):
                if subcommand is not None:
                    raise RuntimeError(
                        "cannot have more than 1 `Subcommand` member"
                    )

                subcommand = (name, argument_type)
                continue

            is_long_option = False
            short: Short | None = None
            help: str | None = None
            default: Any | MISSING = getattr(cls, name, MISSING)

            for data in metadata:
                if data is Long:
                    is_long_option = True
                elif data is Short:
                    # Default to the flag name's first character.
                    short = Short(name[0])
                elif isinstance(data, Short):
                    short = data
                elif isinstance(data, Help):
                    help = data
                else:
                    pass
            else:
                pass

            if is_long_option or short is not None:
                option = Option(
                    name=name,
                    cls=argument_type,
                    short=short,
                    default=default,
                    help=help,
                )

                if name in options.keys():
                    raise RuntimeError(f"option exists: {name}")

                options[name] = option

                if short is not None:
                    if short.value in options.keys():
                        raise RuntimeError(f"option exists: {short.value}")
                    options[short.value] = option
                else:
                    pass
            else:
                arguments.append(
                    Argument(
                        name=name,
                        cls=argument_type,
                        default=default,
                        help=help,
                    )
                )

        return cls(subcommand, arguments, options)


class Command:
    schema: Schema

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if not hasattr(cls, "schema"):
            annotations = inspect.get_annotations(cls)
            cls.schema = Schema.from_annotations(annotations)

        return super().__new__(cls)
