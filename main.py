from datetime import datetime
from glob import glob
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from settings import EntryType, get_settings
from upload import backup
from utils import log


def main():
    settings = get_settings()

    for entry in settings:
        if entry.path is None:
            log("Excluding entry %r", entry.name)
            continue
        if entry.type == EntryType.multiple_files:
            if not entry.zip:
                files = glob(entry.path)
                for file in files:
                    backup(file, entry.folder)
                continue

            buffer = BytesIO()
            files = glob(entry.path)

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

            backup(buffer, entry.folder, filename=entry.zipname)

            backup(entry.path, entry.folder)
        elif entry.type == EntryType.single_file:


if __name__ == "__main__":
    main()
