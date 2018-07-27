import importlib_resources  # type: ignore
import shutil
import sys
import uuid

from configparser import ConfigParser
from pathlib import Path
from tempfile import TemporaryDirectory

from . import pip, bootstrap, zipapp
from .constants import NO_ENTRY_POINT
from .bootstrap.environment import Environment


class UserError(Exception):
    """An exception to wrap errors related to user input."""


def find_entry_point(site_packages: Path, console_script: str) -> str:
    """Find a console_script in a site-packages directory.

    Console script metadata is stored in entry_points.txt per setuptools
    convention. This function searches all entry_points.txt files and
    returns the import string for a given console_script argument.

    :param site_packages: A path to a site-packages directory on disk.
    :param console_script: A console_script string.
    """
    config_parser = ConfigParser()
    config_parser.read(site_packages.rglob("entry_points.txt"))
    return config_parser["console_scripts"][console_script]


def copy_bootstrap(bootstrap_target: Path) -> None:
    """Copy bootstrap code from shiv into the pyz.

    :param bootstrap_target: The temporary directory where we are staging pyz contents.
    """
    for bootstrap_file in importlib_resources.contents(bootstrap):
        if importlib_resources.is_resource(bootstrap, bootstrap_file):
            with importlib_resources.path(bootstrap, bootstrap_file) as f:
                shutil.copyfile(f.absolute(), bootstrap_target / f.name)


def build(output_file, pip_args, compressed=True, python=None, entry_point=None, console_script=None):
    with TemporaryDirectory() as working_path:
        site_packages = Path(working_path, "site-packages")
        site_packages.mkdir(parents=True, exist_ok=True)

        # install deps into staged site-packages
        pip.install(
            ["--target", str(site_packages)] + list(pip_args),
        )

        # if entry_point is a console script, get the callable
        if entry_point is None and console_script is not None:
            try:
                entry_point = find_entry_point(site_packages, console_script)
            except KeyError:
                raise UserError(NO_ENTRY_POINT.format(entry_point=console_script))

        # create runtime environment metadata
        env = Environment(
            build_id=str(uuid.uuid4()),
            entry_point=entry_point,
        )

        Path(working_path, "environment.json").write_text(env.to_json())

        # create bootstrapping directory in working path
        bootstrap_target = Path(working_path, "_bootstrap")
        bootstrap_target.mkdir(parents=True, exist_ok=True)

        # copy bootstrap code
        copy_bootstrap(bootstrap_target)

        # create the zip
        zipapp.create_archive(
            Path(working_path),
            target=Path(output_file),
            interpreter=python or sys.executable,
            main="_bootstrap:bootstrap",
            compressed=compressed,
        )
