from datetime import datetime
import mimetypes
from os import walk
from pathlib import Path
import pickle
import re

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .exceptions import TokenError
from .paths import CREDENTIALS_PATH, LOG_PATH, TOKEN_PATH

SCOPES = ["https://www.googleapis.com/auth/drive"]
ZIP_MIMETYPE = "application/octet-stream"

_EXTRA_MIME_TYPES = (
    ("application/arj", ".arj"),
    ("application/cab", ".cab"),
    ("application/vnd.ms-excel", ".xla"),
    ("application/vnd.ms-powerpoint", ".pot"),
    ("application/x-msaccess", ".mdb"),
    ("application/x-python-code", ".pyc"),
    ("application/x-rar-compressed", ".rar"),
    ("application/x-sqlite3", ".db"),
    ("application/x-sqlite3", ".sqlite"),
    ("application/x-yaml", ".yaml"),
    ("application/x-yaml", ".yml"),
    ("application/xml", ".xml"),
    ("application/zip", ".zip"),
    ("image/x-ms-bmp", ".bmp"),
    ("text/csv", ".csv"),
    ("text/x-php", ".php"),
    ("text/x-python", ".py"),
)


def log(template, *args):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_str = f"[{now}] "
    if isinstance(template, BaseException):
        message = "ERROR: " + repr(template)
    else:
        message = template % args
    with LOG_PATH.open("at", encoding="utf-8") as file_handler:
        file_handler.write(time_str + message + "\n")


def gen_new_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH.as_posix(), SCOPES
    )
    creds = flow.run_local_server(port=0)

    TOKEN_PATH.write_bytes(pickle.dumps(creds))


def get_google_drive_services(creds=None):
    if not creds:
        creds = get_creds_from_token()

    return build("drive", "v3", credentials=creds)


def get_creds_from_token():
    if not TOKEN_PATH.exists():
        exc = TokenError(f"{TOKEN_PATH.as_posix()!r} doesn't exist")
        log(exc)
        raise exc

    creds = pickle.loads(TOKEN_PATH.read_bytes())

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            log("Token updated (expires %s)", creds.expiry)
            TOKEN_PATH.write_bytes(pickle.dumps(creds))
        else:
            exc = TokenError(f"Invalid token: {TOKEN_PATH.as_posix()!r}")
            log(exc)
            raise exc

    return creds


def get_mimetype(filepath: str) -> str:
    """Returns the mimetype of the `filepath` based on its extension.

    Args:
        filepath (str): input filepath.

    Returns:
        str: mimetype of `filepath`.
    """

    return mimetypes.guess_type(filepath)[0] or "application/octet-stream"


def _improve_mimetypes():
    for mime_type, extension in _EXTRA_MIME_TYPES:
        mimetypes.add_type(mime_type, extension, strict=True)


def list_files(root_path, regex_filter):
    root_path = Path(root_path).absolute()
    pattern = re.compile(regex_filter, re.IGNORECASE)
    files = []

    for root, _, temp_files in walk(root_path.as_posix()):
        for file in temp_files:
            filepath = Path(root).joinpath(file)
            if pattern.search(filepath.as_posix()):
                files.append(filepath)

    return files


_improve_mimetypes()
