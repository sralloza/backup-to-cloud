from io import BytesIO
import mimetypes
from pathlib import Path
from typing import Union

from googleapiclient.http import MediaIoBaseUpload

from .utils import get_google_drive_services, get_mimetype, log

FileData = Union[Path, str, BytesIO]


def backup(file_data: FileData, mimetype, folder=None, filename=None):
    if isinstance(file_data, (str, Path)):
        filepath = Path(file_data)
        if not filepath.exists():
            raise FileNotFoundError(filepath.as_posix())

        filename = filename or filepath.name
        file_data = BytesIO(filepath.read_bytes())
        del filepath

    service = get_google_drive_services()
    file_metadata = {"name": filename, "mimeType": mimetype}
    query = "name = %r" % (filename)

    if folder:
        file_metadata["parents"] = [folder]
        query += " and %r in parents" % (folder)

    response = service.files().list(q=query, fields="files(id, name)",).execute()
    ids = [x.get("id") for x in response.get("files", [])]

    if len(ids) > 1:
        raise RuntimeError("Files should not be more than one")

    if ids:
        return save_version(service, file_data, mimetype, ids[0], filename)
    return save_new_file(service, file_data, mimetype, folder, filename)


def save_new_file(gds, file_data: BytesIO, mimetype, folder=None, filename=None):
    log("saving new file: %s", filename)
    file_metadata = {"name": filename, "mimeType": mimetype}

    if folder:
        file_metadata["parents"] = [folder]

    media = MediaIoBaseUpload(file_data, mimetype=mimetype)
    res = (
        gds.files().create(body=file_metadata, media_body=media, fields="id").execute()
    )
    return res


def save_version(gds, file_data: BytesIO, mimetype, file_id: str, filename=None):
    log("saving new version of %s", filename)
    file_metadata = {
        "name": filename,
        "published": True,
    }
    media = MediaIoBaseUpload(file_data, mimetype=mimetype)
    response = (
        gds.files()
        .update(
            fileId=file_id,
            keepRevisionForever=False,
            body=file_metadata,
            media_body=media,
        )
        .execute()
    )

    return response
