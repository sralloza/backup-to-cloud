from datetime import datetime
import mimetypes
import os
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


def log(template, *args):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_str = f"[{now}] "
    message = template % args
    with LOG_PATH.open("at", encoding="utf-8") as file_handler:
        file_handler.write(time_str + message + "\n")


def gen_token(creds):
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
        log(str(exc))
        raise exc

    creds = pickle.loads(TOKEN_PATH.read_bytes())

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            log("Token updated (expires %s)", creds.expiry)
            TOKEN_PATH.write_bytes(pickle.dumps(creds))
        else:
            exc = TokenError(f"Invalid token: {TOKEN_PATH.as_posix()!r}")
            log(str(exc))
            raise exc

    return creds


def get_mimetype(filepath: str) -> str:
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype:
        return mimetype

    data = Path(filepath).read_bytes()
    try:
        data.decode()
    except UnicodeDecodeError:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return "application/octet-stream"

    return "text/plain"


def list_files(root_path, regex_filter):
    root_path = Path(root_path).absolute()
    pattern = re.compile(regex_filter, re.IGNORECASE)
    files = []

    for root, _, temp_files in os.walk(root_path.as_posix()):
        for file in temp_files:
            filepath = Path(root).joinpath(file)
            if pattern.search(filepath.as_posix()):
                files.append(filepath)

    return files
