import argparse
import sys
from datetime import datetime
from glob import glob
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from .settings import EntryType, get_settings
from .upload import backup
from .utils import get_mimetype, list_files, log, ZIP_MIMETYPE


def _main():
    settings = get_settings()

    for entry in settings:
        if entry.root_path is None:
            log("Excluding entry %r", entry.name)
            continue
        if entry.type == EntryType.multiple_files:
            if not entry.zip:
                files = list_files(entry.root_path, entry.filter)
                for file in files:
                    mimetype = get_mimetype(file)
                    backup(file, mimetype, entry.folder)
                continue

            buffer = BytesIO()
            files = list_files(entry.root_path, entry.filter)

            if not files:
                raise RuntimeError(
                    "Not files found for entry %r (path=%r, filter=%r)"
                    % (entry.name, entry.root_path, entry.filter)
                )

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
                    myzip.write(file, Path(file).relative_to(min_file))

            backup(buffer, ZIP_MIMETYPE, entry.folder, filename=entry.zipname)

        elif entry.type == EntryType.single_file:
            mimetype = get_mimetype(entry.root_path)
            backup(entry.root_path, mimetype, entry.folder)


def main():
    args = vars(parse_args())
    if args["command"] == "check-regex":
        files = list_files(args["root-path"], args["regex"])
        for file in files:
            print(file)
        sys.exit(0)

    else:
        _main()


def parse_args():
    parser = argparse.ArgumentParser("backup-to-cloud")
    subparsers = parser.add_subparsers(dest="command")
    check_regex_parser = subparsers.add_parser("check-regex")
    check_regex_parser.add_argument("root-path")
    check_regex_parser.add_argument("regex", default=".", nargs="?")
    return parser.parse_args()


if __name__ == "__main__":
    main()
