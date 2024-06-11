import pathlib
from typing import Annotated

import clap

parser = clap.Application()


def clone(
    repository: str,
    directory: pathlib.Path,
    *,
    template: pathlib.Path,
    local: Annotated[bool, clap.Short],
) -> None:
    """Clone a repository into a new directory.

    Clones a repository into a newly created directory, creates
    remote-tracking branches for each branch in the cloned repository (visible
    using git branch --remotes), and creates and checks out an initial branch
    that is forked from the cloned repository’s currently active branch.

    After the clone, a plain git fetch without arguments will update all the
    remote-tracking branches, and a git pull without arguments will in addition
    merge the remote master branch into the current master branch, if any
    (this is untrue when --single-branch is given; see below).

    This default configuration is achieved by creating references to the remote
    branch heads under refs/remotes/origin and by initializing
    remote.origin.url and remote.origin.fetch configuration variables.

    Parameters
    ----------
    repository:
        Brief description about the `repository` argument.
    directory:
        Brief description about the `directory` argument.

    Other Parameters
    ----------------
    template:
        Brief description about the `template` option.
    local:
        Brief description about the `local` option.

    Examples
    --------
    >>> print("Hello, World!")
    Hello, World!
    """
    raise NotImplementedError


clone_1 = clap.command()(clone)

clone_2 = (
    clap.CommandBuilder(clone)
    .set_brief("Clone a repository into a new directory.")
    .set_description("""
        Clones a repository into a newly created directory, creates
        remote-tracking branches for each branch in the cloned repository
        (visible using git branch --remotes), and creates and checks out an
        initial branch that is forked from the cloned repository’s currently
        active branch.

        After the clone, a plain git fetch without arguments will update all
        the remote-tracking branches, and a git pull without arguments will in
        addition merge the remote master branch into the current master branch,
        if any (this is untrue when --single-branch is given; see below).

        This default configuration is achieved by creating references to the
        remote branch heads under refs/remotes/origin and by initializing
        remote.origin.url and remote.origin.fetch configuration variables.
    """)
    .add_argument(
        argument=clap.Argument(
            name="repository",
            cls=str,
            brief="Brief description about the `repository` argument.",
        )
    )
    .add_argument(
        argument=clap.Argument(
            name="directory",
            cls=pathlib.Path,
            brief="Brief description about the `repository` argument.",
        )
    )
    .add_option(
        option=clap.Option(
            name="template",
            cls=str,
            brief="Brief description about the `template` option.",
        )
    )
    .add_option(
        option=clap.Option(
            name="local",
            cls=bool,
            brief="Brief description about the `local` option.",
        )
    )
    .build()
)


@clap.command()
def init() -> None:
    raise NotImplementedError
