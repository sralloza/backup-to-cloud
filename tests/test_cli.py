"""Main module to handle start of execution."""

from unittest import mock

from click.testing import CliRunner
import pytest

from backup_to_cloud.cli import main
from backup_to_cloud.cli import cli


@pytest.mark.parametrize("arg", ["-h", "--help"])
def test_help(arg):
    runner = CliRunner()
    result = runner.invoke(main, [arg])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "Options:" in result.stdout
    assert "Commands:" in result.stdout


@pytest.mark.parametrize("args", [["<root-path>"], ["<root-path>", "<regex>"]])
@mock.patch("backup_to_cloud.cli.list_files")
def test_check_regex_command(list_files_m, args):
    list_files_m.return_value.__iter__.return_value = list("abcdef")

    runner = CliRunner()
    result = runner.invoke(main, ["check-regex"] + args)

    assert result.exit_code == 0
    assert result.output == "\n".join("abcdef") + "\n"

    if len(args) == 1:
        list_files_m.assert_called_once_with("<root-path>", ".")
    else:
        list_files_m.assert_called_once_with("<root-path>", "<regex>")


@mock.patch("backup_to_cloud.cli.gen_new_token")
def test_gen_token_command(gen_new_token_m):
    runner = CliRunner()
    result = runner.invoke(main, ["gen-token"])

    assert result.exit_code == 0
    assert result.output == ""
    gen_new_token_m.assert_called_once_with()


@mock.patch("backup_to_cloud.cli.create_backup")
def test_create_backup_command(create_backup_m):
    runner = CliRunner()
    result = runner.invoke(main, ["create-backup"])

    assert result.exit_code == 0
    assert result.output == ""
    create_backup_m.assert_called_once_with()


@mock.patch("backup_to_cloud.cli.main")
def test_cli(main_m):
    cli()
    main_m.assert_called_once_with(prog_name="backup-to-cloud")
