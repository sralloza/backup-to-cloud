from glob import glob
from io import BytesIO
import mimetypes
from pathlib import Path
import pickle
from time import asctime
from zipfile import ZipFile

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import MediaFileUpload, build
from googleapiclient.http import MediaIoBaseUpload

from settings import EntryType, get_settings

# If modifying these scopes, delete the file token.pickle.
CREDENTIALS_PATH = Path(__file__).with_name("credentials.json")
FOLDER = "1hrW_dUEPt-YuhErDxOj-uRkGA5u3jMaA"
LOG_PATH = Path(__file__).with_name("cloud-backup.log")
SCOPES = ["https://www.googleapis.com/auth/drive"]
SETTINGS_PATH = Path(__file__).with_name(".settings.yml")
TOKEN_PATH = Path(__file__).with_name("token.pickle")


def log(template, *args):
    time_str = f"[{asctime()}] "
    message = template % args
    with LOG_PATH.open("at", encoding="utf-8") as file_handler:
        file_handler.write(time_str + message + "\n")


class TokenError(Exception):
    pass


def backup(file_path: str, folder=None, filename=None):
    if isinstance(file_path, BytesIO):
        filepath = file_path
    else:
        filepath = Path(file_path).absolute()
        filename = filepath.name

        if not filepath.exists():
            raise FileNotFoundError(filepath.as_posix())

    service = get_google_drive_services()
    mimetype = mimetypes.guess_type(filename)[0]
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
        return save_version(service, filepath, ids[0], filename)
    return save_new_file(service, filepath, folder, filename)


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


def main():
    settings = get_settings(SETTINGS_PATH)[:-1]

    for entry in settings:
        if entry.type == EntryType.folder:
            if not entry.zip:
                files = glob(entry.path)
                responses = []
                for file in files:
                    res = backup(file, entry.folder)
                return all(responses)

            buffer = BytesIO()
            files = glob(entry.path)

            with ZipFile(buffer, "w") as myzip:
                for file in files:
                    myzip.write(file, Path(file).name)

            filename = Path(entry.path).parts[-2] + ".zip"
            return backup(buffer, entry.folder, filename=filename)
            # zipfile_ob = zipfile.ZipFile(file_like_object)

        elif entry.type == EntryType.file:
            backup(entry.path, entry.folder)


def save_new_file(gds, filepath: Path, folder=None, filename=None):
    if isinstance(filepath, BytesIO):
        pass
    else:
        filename = filepath.name
        filepath = filepath.as_posix()

    log("saving new file: %s", filepath)
    mimetype = mimetypes.guess_type(filename)[0]
    file_metadata = {"name": filename, "mimeType": mimetype}

    if folder:
        file_metadata["parents"] = [folder]

    media = MediaIoBaseUpload(filepath, mimetype=mimetype)
    res = (
        gds.files().create(body=file_metadata, media_body=media, fields="id").execute()
    )
    return res


def save_version(gds, filepath: Path, file_id: str, filename=None, keep_revision_forever=False):
    log("saving new version of %s", filepath)

    if isinstance(filepath, BytesIO):
        pass
    else:
        filename = filepath.name
        filepath = filepath.as_posix()

    file_metadata = {
        "name": filename,
        "published": True,
    }
    mimetype = mimetypes.guess_type(filename)[0]
    media = MediaIoBaseUpload(filepath, mimetype=mimetype)
    response = (
        gds.files()
        .update(
            fileId=file_id,
            keepRevisionForever=keep_revision_forever,
            body=file_metadata,
            media_body=media,
        )
        .execute()
    )

    return response


if __name__ == "__main__":
    main()
