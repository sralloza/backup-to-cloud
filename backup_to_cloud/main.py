"""Main module to handle start of execution."""

from io import BytesIO
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

import click

from .exceptions import NoFilesFoundError, SettingsError
from .settings import EntryType, get_settings
from .upload import backup
from .utils import ZIP_MIMETYPE, get_mimetype, list_files, log


def create_backup(dry_run=False):
    """Real main function.

    Args:
        dry_run (bool, optional): if True, it won't upload anything to google
            drive. Designed to check settings. Defaults to True.

    Raises:
        FileNotFoundError: if a file is not found in the filesystem.
        NoFilesFoundError: if the system is supposed to find multiple
            files and it doesn't find any files.

    """

    settings = get_settings()

    for entry in settings:
        if entry.root_path is None:
            log("Excluding entry %r", entry.name)
            continue

        if entry.type == EntryType.multiple_files:
            files = list_files(entry.root_path, entry.filter)

            for file in files:
                if not Path(file).is_file():
                    raise FileNotFoundError(file)

            if not files:
                raise NoFilesFoundError(
                    "No files found for entry %r (path=%r, filter=%r)"
                    % (entry.name, entry.root_path, entry.filter)
                )

            if not entry.zip:
                for file in files:
                    mimetype = get_mimetype(file)
                    backup(file, mimetype, entry.folder, dry_run=dry_run)
                continue

            buffer = BytesIO()
            min_file = min(files)
            max_file = max(files)

            while True:
                try:
                    Path(max_file).relative_to(min_file)
                    break
                except ValueError:
                    min_file = Path(min_file).parent.as_posix()

            with ZipFile(buffer, "w") as myzip:
                for file in files:
                    arcname = Path(file).relative_to(min_file).as_posix()
                    myzip.write(file, arcname=arcname)

            backup(
                buffer,
                ZIP_MIMETYPE,
                entry.folder,
                filename=entry.zipname,
                dry_run=dry_run,
            )

        elif entry.type == EntryType.single_file:
            mimetype = get_mimetype(entry.root_path)
            backup(entry.root_path, mimetype, entry.folder, dry_run=dry_run)
        else:
            raise SettingsError(f"Invalid EntryType: {entry.type!r}")


def check_settings():
    """Checks that the settings are valid."""

    zipfile_mocker = mock.patch(__name__ + ".ZipFile")
    zipfile_mocker.start()

    try:
        create_backup(dry_run=True)
    except Exception as exc:
        excname = type(exc).__name__
        msg = f"{excname}: {exc}"
        click.secho(msg, err=True, fg="bright_red")
    else:
        click.secho("settings ok", fg="bright_green")
    finally:
        zipfile_mocker.stop()
