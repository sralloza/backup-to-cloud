from pathlib import Path
from unittest import mock

import pytest

from backup_to_cloud.exceptions import SettingsError, TokenError
from backup_to_cloud.utils import (
    SCOPES,
    ZIP_MIMETYPE,
    gen_new_token,
    get_creds_from_token,
    get_google_drive_services,
    get_mimetype,
    list_files,
    log,
)


def test_module_constants():
    assert isinstance(SCOPES, list)
    assert len(SCOPES) == 1
    assert isinstance(SCOPES[0], str)
    assert "googleapis" in SCOPES[0]

    assert isinstance(ZIP_MIMETYPE, str)


class TestLog:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.dt_m = mock.patch("backup_to_cloud.utils.datetime").start()
        self.log_path_m = mock.patch("backup_to_cloud.utils.LOG_PATH").start()

        yield
        mock.patch.stopall()

    exceptions = (
        None,
        ValueError("Invalid value"),
        TokenError("Invalid token"),
        SettingsError("Invalid settings"),
    )

    @pytest.mark.parametrize("exc", exceptions)
    def test_log(self, exc):
        self.dt_m.now.return_value.strftime.return_value = "<datetime>"
        if exc:
            log(exc)
            msg = "[<datetime>] ERROR: " + repr(exc)
        else:
            log("this is %d%% %r important", 100, "really")
            msg = "[<datetime>] this is 100% 'really' important"

        self.dt_m.now.return_value.strftime.assert_called_once_with("%Y-%m-%d %H:%M:%S")
        self.log_path_m.open.assert_called_once_with("at", encoding="utf-8")
        file_handler = self.log_path_m.open.return_value
        file_handler.__enter__.assert_called_once()
        file_handler.__enter__.return_value.write.assert_called_once_with(msg + "\n")
        file_handler.__exit__.assert_called_once()


class TestGenNewToken:
    @pytest.fixture(autouse=True)
    def mocks(self):
        secrets_path = "backup_to_cloud.utils.InstalledAppFlow.from_client_secrets_file"
        self.fcsf_m = mock.patch(secrets_path).start()
        self.creds_path_m = mock.patch("backup_to_cloud.utils.CREDENTIALS_PATH").start()
        self.scopes_m = mock.patch("backup_to_cloud.utils.SCOPES").start()
        self.token_path_m = mock.patch("backup_to_cloud.utils.TOKEN_PATH").start()
        self.pkl_dumps_m = mock.patch("backup_to_cloud.utils.pickle.dumps").start()

        yield
        mock.patch.stopall()

    @pytest.mark.parametrize("exists", [True, False])
    def test_gen_new_token(self, exists):
        self.creds_path_m.exists.return_value = exists
        self.creds_path_m.as_posix.return_value = "<creds-path>"

        if not exists:
            with pytest.raises(FileNotFoundError, match="<creds-path>"):
                gen_new_token()
            self.fcsf_m.assert_not_called()
            return

        gen_new_token()

        self.fcsf_m.assert_called_once_with(
            self.creds_path_m.as_posix.return_value, self.scopes_m
        )
        self.fcsf_m.return_value.run_local_server.assert_called_once_with(port=0)
        flow = self.fcsf_m.return_value.run_local_server.return_value

        self.pkl_dumps_m.assert_called_once_with(flow)
        self.token_path_m.write_bytes.assert_called_once_with(
            self.pkl_dumps_m.return_value
        )


@pytest.mark.parametrize("creds", [None, "<creds>"])
@mock.patch("backup_to_cloud.utils.get_creds_from_token")
@mock.patch("backup_to_cloud.utils.build")
def test_get_google_drive_services(build_m, gcft_m, creds):
    get_google_drive_services(creds)

    if not creds:
        gcft_m.assert_called_once_with()
        build_m.assert_called_once_with("drive", "v3", credentials=gcft_m.return_value)
    else:
        gcft_m.assert_not_called()
        build_m.assert_called_once_with("drive", "v3", credentials="<creds>")


class TestGetCredsFromToken:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.token_path_m = mock.patch("backup_to_cloud.utils.TOKEN_PATH").start()
        self.pkl_loads_m = mock.patch("backup_to_cloud.utils.pickle.loads").start()
        self.pkl_dumps_m = mock.patch("backup_to_cloud.utils.pickle.dumps").start()
        self.log_m = mock.patch("backup_to_cloud.utils.log").start()
        self.req_m = mock.patch("backup_to_cloud.utils.Request").start()

        self.token_path_m.as_posix.return_value = "<token-path>"
        self.token_path_m.read_bytes.return_value = b"<pickle-data>"

        yield

        mock.patch.stopall()

    @pytest.fixture(params=[True, False])
    def valid(self, request):
        return request.param

    @pytest.fixture(params=[True, False])
    def exists(self, request):
        return request.param

    @pytest.fixture(params=[True, False])
    def expired(self, request):
        return request.param

    @pytest.fixture(params=[None, "<refresh-token>"])
    def refresh_token(self, request):
        return request.param

    def test_get_creds_from_token(self, exists, valid, expired, refresh_token):
        self.token_path_m.exists.return_value = exists
        self.pkl_loads_m.return_value.valid = valid
        self.pkl_loads_m.return_value.expired = expired
        self.pkl_loads_m.return_value.refresh_token = refresh_token

        do_refresh = expired and bool(refresh_token) and not valid and exists
        error = not valid and (not expired or not bool(refresh_token)) and exists

        if not exists:
            with pytest.raises(TokenError, match="'<token-path>' doesn't exist") as exc:
                get_creds_from_token()

            self.pkl_loads_m.assert_not_called()
            self.pkl_dumps_m.assert_not_called()
            self.log_m.assert_called_with(exc.value)
            return

        if error:
            with pytest.raises(
                TokenError, match="Invalid token: '<token-path>'"
            ) as exc:
                get_creds_from_token()

            self.pkl_loads_m.assert_called_once_with(b"<pickle-data>")
            self.pkl_dumps_m.assert_not_called()
            self.log_m.assert_called_with(exc.value)
            return

        creds = get_creds_from_token()
        assert creds == self.pkl_loads_m.return_value

        self.pkl_loads_m.assert_called_once_with(b"<pickle-data>")

        if do_refresh:
            self.req_m.assert_called_once_with()
            self.pkl_loads_m.return_value.refresh.assert_called_once_with(
                self.req_m.return_value
            )
            self.pkl_dumps_m.assert_called_once_with(self.pkl_loads_m.return_value)
            self.log_m.assert_called_once_with(
                "Token updated (expires %s)", self.pkl_loads_m.return_value.expiry
            )


@mock.patch("backup_to_cloud.utils.log")
def test_get_mimetype(log_m):
    test = get_mimetype
    assert test("folder/file.arj") == "application/arj"
    assert test("folder/file.bmp") == "image/x-ms-bmp"
    assert test("folder/file.cab") == "application/cab"
    assert test("folder/file.csv") == "text/csv"
    assert test("folder/file.db") == "application/x-sqlite3"
    assert test("folder/file.doc") == "application/msword"
    assert test("folder/file.doc") == "application/msword"
    assert (
        test("folder/file.docm") == "application/vnd.ms-word.document.macroEnabled.12"
    )
    assert (
        test("folder/file.docx")
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert test("folder/file.dot") == "application/msword"
    assert (
        test("folder/file.dotm") == "application/vnd.ms-word.template.macroEnabled.12"
    )
    assert (
        test("folder/file.dotx")
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.template"
    )
    assert test("folder/file.gif") == "image/gif"
    assert test("folder/file.htm") == "text/html"
    assert test("folder/file.html") == "text/html"
    assert test("folder/file.jpg") == "image/jpeg"
    assert test("folder/file.js") == "application/javascript"
    assert test("folder/file.mdb") == "application/x-msaccess"
    assert test("folder/file.mp3") == "audio/mpeg"
    assert test("folder/file.ods") == "application/vnd.oasis.opendocument.spreadsheet"
    assert test("folder/file.pdf") == "application/pdf"
    assert test("folder/file.php") == "text/x-php"
    assert test("folder/file.png") == "image/png"
    assert test("folder/file.pot") == "application/vnd.ms-powerpoint"
    assert (
        test("folder/file.potm")
        == "application/vnd.ms-powerpoint.template.macroEnabled.12"
    )
    assert (
        test("folder/file.potx")
        == "application/vnd.openxmlformats-officedocument.presentationml.template"
    )
    assert test("folder/file.ppa") == "application/vnd.ms-powerpoint"
    assert (
        test("folder/file.ppam")
        == "application/vnd.ms-powerpoint.addin.macroEnabled.12"
    )
    assert test("folder/file.pps") == "application/vnd.ms-powerpoint"
    assert (
        test("folder/file.ppsm")
        == "application/vnd.ms-powerpoint.slideshow.macroEnabled.12"
    )
    assert (
        test("folder/file.ppsx")
        == "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
    )
    assert test("folder/file.ppt") == "application/vnd.ms-powerpoint"
    assert (
        test("folder/file.pptm")
        == "application/vnd.ms-powerpoint.presentation.macroEnabled.12"
    )
    assert (
        test("folder/file.pptx")
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert test("folder/file.py") == "text/x-python"
    assert test("folder/file.pyc") == "application/x-python-code"
    assert test("folder/file.rar") == "application/x-rar-compressed"
    assert test("folder/file.sh") == "application/x-sh"
    assert test("folder/file.sqlite") == "application/x-sqlite3"
    assert test("folder/file.swf") == "application/x-shockwave-flash"
    assert test("folder/file.tar") == "application/x-tar"
    assert test("folder/file.toml") == "application/toml"
    assert test("folder/file.txt") == "text/plain"
    assert test("folder/file.xla") == "application/vnd.ms-excel"
    assert test("folder/file.xlam") == "application/vnd.ms-excel.addin.macroEnabled.12"
    assert test("folder/file.xls") == "application/vnd.ms-excel"
    assert (
        test("folder/file.xlsb")
        == "application/vnd.ms-excel.sheet.binary.macroEnabled.12"
    )
    assert test("folder/file.xlsm") == "application/vnd.ms-excel.sheet.macroEnabled.12"
    assert (
        test("folder/file.xlsx")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert test("folder/file.xlt") == "application/vnd.ms-excel"
    assert (
        test("folder/file.xltm") == "application/vnd.ms-excel.template.macroEnabled.12"
    )
    assert (
        test("folder/file.xltx")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.template"
    )
    assert test("folder/file.xml") == "application/xml"
    assert test("folder/file.yaml") == "application/x-yaml"
    assert test("folder/file.yml") == "application/x-yaml"
    assert test("folder/file.zip") == "application/zip"
    assert test("folder/file.unknown") == "application/octet-stream"

    assert log_m.call_count == 57


@mock.patch("backup_to_cloud.utils.walk")
def test_list_files(walk_m):
    walk_m.return_value = (
        ("/home/test", ["index", "public"], []),
        ("/home/test/index", ["a"], ["access.log", "error.log"]),
        ("/home/test/index/a", ["x"], ["a.txt"]),
        ("/home/test/index/a/x", [], ["file.txt", "file.pdf"]),
        ("/home/test/public", [], ["access.log", "error.log"]),
    )

    all_files = list_files("<root>", ".")
    assert set(all_files) == {
        Path("/home/test/index/a/a.txt"),
        Path("/home/test/index/a/x/file.txt"),
        Path("/home/test/index/a/x/file.pdf"),
        Path("/home/test/index/access.log"),
        Path("/home/test/index/error.log"),
        Path("/home/test/public/access.log"),
        Path("/home/test/public/error.log"),
    }

    log_files = list_files("<root>", ".log$")

    assert set(log_files) == {
        Path("/home/test/index/access.log"),
        Path("/home/test/index/error.log"),
        Path("/home/test/public/access.log"),
        Path("/home/test/public/error.log"),
    }

    txt_files = list_files("<root>", ".txt$")
    assert set(txt_files) == {
        Path("/home/test/index/a/a.txt"),
        Path("/home/test/index/a/x/file.txt"),
    }

    pdf_files = list_files("<root>", ".pdf$")
    assert set(pdf_files) == {Path("/home/test/index/a/x/file.pdf")}
