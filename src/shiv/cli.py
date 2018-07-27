import sys

from typing import Optional, List

import click

from .builder import build, UserError
from .constants import SHIV, NO_PIP_ARGS, NO_OUTFILE, DISALLOWED_PIP_ARGS, BLACKLISTED_ARGS

__version__ = '0.0.28'


@click.command(
    context_settings=dict(
        help_option_names=["-h", "--help", "--halp"], ignore_unknown_options=True
    )
)
@click.version_option(version=__version__, prog_name='shiv')
@click.option("--entry-point", "-e", default=None, help="The entry point to invoke.")
@click.option(
    "--console-script", "-c", default=None, help="The console_script to invoke."
)
@click.option("--output-file", "-o", help="The file for shiv to create.")
@click.option("--python", "-p", help="The path to a python interpreter to use.")
@click.option(
    "--compressed/--uncompressed",
    default=True,
    help="Whether or not to compress your zip.",
)
@click.argument("pip_args", nargs=-1, type=click.UNPROCESSED)
def main(
    output_file: str,
    entry_point: Optional[str],
    console_script: Optional[str],
    python: Optional[str],
    compressed: bool,
    pip_args: List[str],
) -> None:
    """
    Shiv is a command line utility for building fully self-contained Python zipapps
    as outlined in PEP 441, but with all their dependencies included!
    """
    quiet = "-q" in pip_args or '--quiet' in pip_args

    if not quiet:
        click.secho(" shiv! " + SHIV, bold=True)

    if not pip_args:
        sys.exit(NO_PIP_ARGS)

    if output_file is None:
        sys.exit(NO_OUTFILE)

    # check for disallowed pip arguments
    for blacklisted_arg in BLACKLISTED_ARGS:
        for supplied_arg in pip_args:
            if supplied_arg in blacklisted_arg:
                sys.exit(
                    DISALLOWED_PIP_ARGS.format(
                        arg=supplied_arg, reason=BLACKLISTED_ARGS[blacklisted_arg]
                    )
                )

    # create the pyz
    try:
        build(output_file, pip_args, compressed, python, entry_point, console_script)
    except UserError as e:
        sys.exit(str(e))

    if not quiet:
        click.secho(" done ", bold=True)
