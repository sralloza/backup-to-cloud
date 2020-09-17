"""Handles the upload of files to Google Drive via Google Drive API v3."""

from io import BytesIO
from pathlib import Path
from typing import Union

from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import Resource

from .exceptions import MultipleFilesError
from .utils import get_google_drive_services, log

FD = Union[Path, str, BytesIO]


def backup(file_data: FD, mimetype: str, folder_id: str, filename: str = None) -> dict:
    """Backups the file.

    Args:
        file_data (FD): file data. Can be a Path instance pointing to the
            actual file, a str containing the filepath or a BytesIO instance
            containing the file content.
        mimetype (str): MIME type of the file.
        folder_id (str): id of the Google Drive folder to upload the file to.
            To select the root folder, put `folder_id='root`.
        filename (str, optional): name of the file. If None, the filename will be
            generated from the filepath (if `file_data` is str or Path). Defaults to None.

    Raises:
        FileNotFoundError: if `file_data` is str or Path and the filepath doesn't exist.
        ValueError: if `file_data` is BytesIO and `filename` is undefined.
        MultipleFilesError: if there is more than one file in the target folder named ``filename``.

    Returns:
        dict: metadata of the file uploaded.
    """

    if isinstance(file_data, (str, Path)):
        filepath = Path(file_data)
        if not filepath.exists():
            exc = FileNotFoundError(filepath.as_posix())
            log(exc)
            raise exc

        filename = filename or filepath.name
        file_data = BytesIO(filepath.read_bytes())
        del filepath
    else:
        if not filename:
            exc = ValueError("If file_data is BytesIO, filename is required")
            log(exc)
            raise exc

    service = get_google_drive_services()
    query = f"name = {filename!r} and {folder_id!r} in parents"

    # pylint: disable=E1101
    response = service.files().list(q=query, fields="files(id, name)").execute()
    ids = [x.get("id") for x in response.get("files", [])]

    if len(ids) > 1:
        msg = (
            "Detected more than one file named "
            f"{filename!r} in the target folder {ids!r}"
        )
        exc = MultipleFilesError(msg)
        log(exc)
        raise exc

    if ids:
        return save_version(service, file_data, mimetype, ids[0], filename)
    return save_new_file(service, file_data, mimetype, folder_id, filename)


def save_new_file(
    gds: Resource, file_data: BytesIO, mimetype: str, folder_id: str, filename: str
) -> dict:
    """Uploads a new file to Google Drive.

    Args:
        gds (Resource): google drive service.
        file_data (BytesIO): file content as a buffer.
        mimetype (str): MIME type of the file.
        folder_id (str): Google Drive's id of the folder.
        filename (str): filename of the file.

    Returns:
        dict: metadata of the uploaded file.
    """

    log("Saving new file: %s", filename)
    file_metadata = {"name": filename, "mimeType": mimetype, "parents": [folder_id]}

    media = MediaIoBaseUpload(file_data, mimetype=mimetype)
    res = (
        gds.files().create(body=file_metadata, media_body=media, fields="id").execute()
    )
    return res


def save_version(
    gds: Resource, file_data: BytesIO, mimetype: str, file_id: str, filename: str
) -> dict:
    """Uploads a new version of an existing file to Google Drive.

    Args:
        gds (Resource): google drive services.
        file_data (BytesIO): file content as a buffer.
        mimetype (str): MIME type of the file.
        file_id (str): Google Drive's id of the existing file.
        filename (str): filename of the file.

    Returns:
        dict: metadata of the uploaded file.
    """

    log("Saving new version of %s", filename)
    media = MediaIoBaseUpload(file_data, mimetype=mimetype)
    response = (
        gds.files()
        .update(fileId=file_id, keepRevisionForever=False, media_body=media)
        .execute()
    )

    return response
