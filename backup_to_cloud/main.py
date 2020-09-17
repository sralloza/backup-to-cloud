"""Main module to handle start of execution."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from .exceptions import NoFilesFoundError, SettingsError
from .settings import EntryType, get_settings
from .upload import backup
from .utils import ZIP_MIMETYPE, get_mimetype, list_files, log


def create_backup():
    """Real main function."""
    settings = get_settings()

    for entry in settings:
        if entry.root_path is None:
            log("Excluding entry %r", entry.name)
            continue

        if entry.type == EntryType.multiple_files:
            files = list_files(entry.root_path, entry.filter)

            if not files:
                raise NoFilesFoundError(
                    "No files found for entry %r (path=%r, filter=%r)"
                    % (entry.name, entry.root_path, entry.filter)
                )

            if not entry.zip:
                for file in files:
                    mimetype = get_mimetype(file)
                    backup(file, mimetype, entry.folder)
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

            backup(buffer, ZIP_MIMETYPE, entry.folder, filename=entry.zipname)

        elif entry.type == EntryType.single_file:
            mimetype = get_mimetype(entry.root_path)
            backup(entry.root_path, mimetype, entry.folder)
        else:
            raise SettingsError(f"Invalid EntryType: {entry.type!r}")
