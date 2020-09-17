"""Handles the Command Line Interface."""

import click

from .utils import gen_new_token, list_files
from .main import create_backup

CTX_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CTX_SETTINGS)
def main():
    """Uploads backups to google drive"""


@main.command("check-regex")
@click.argument("root-path")
@click.argument("regex", default=".", required=False)
def check_regex_command(root_path, regex):
    """Checks which files are catched by a regex"""

    files = list_files(root_path, regex)
    for file in files:
        print(file)


@main.command("gen-token")
def gen_token_command():
    """Generates a new token"""

    gen_new_token()


@main.command("create-backup")
def create_backup_command():
    """Creates a backup and uploads it to google drive"""

    create_backup()


def cli():
    """Calls the main program setting the correct name"""
    return main(prog_name="backup-to-cloud")  # pylint: disable=unexpected-keyword-arg
