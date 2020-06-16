
from datetime import datetime
import mimetypes
from pathlib import Path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from paths import CREDENTIALS_PATH, LOG_PATH, SCOPES, TOKEN_PATH



class TokenError(Exception):
    pass


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


def get_mimetype(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"

def list_files(regex):
    real_regex = Path(regex)
