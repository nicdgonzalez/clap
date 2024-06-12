import clap

test_option = clap.Option(
    name="help",
    brief="Shows this help message then exits.",
    alias="h",
)

test_positional = clap.Positional(
    name="name",
    brief="The name of the Minecraft server to open.",
    target_type=str,
    default="fuji",
    n_args=(1,)
)

assert isinstance(test_option, (clap.ParameterizedArgument,))