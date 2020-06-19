from argparse import Namespace
import random
import shlex
from unittest import mock

import pytest

from backup_to_cloud.exceptions import NoFilesFoundError, SettingsError
from backup_to_cloud.main import _main, main, parse_args
from backup_to_cloud.settings import BackupEntry
from backup_to_cloud.utils import ZIP_MIMETYPE


class TestHiddenMain:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.backup_m = mock.patch("backup_to_cloud.main.backup").start()
        self.get_mt_m = mock.patch("backup_to_cloud.main.get_mimetype").start()
        self.get_settings_m = mock.patch("backup_to_cloud.main.get_settings").start()
        self.list_files_m = mock.patch("backup_to_cloud.main.list_files").start()
        self.zipfile_m = mock.patch("backup_to_cloud.main.ZipFile").start()
        self.bytesio_m = mock.patch("backup_to_cloud.main.BytesIO").start()
        self.log_m = mock.patch("backup_to_cloud.main.log").start()

        yield

        mock.patch.stopall()

    def test_no_root_path(self):
        entry = BackupEntry("<name>", "single-file", None, "<folder-id>")
        self.get_settings_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"

        _main()

        self.backup_m.assert_not_called()
        self.get_mt_m.assert_not_called()
        self.get_settings_m.assert_called_once_with()
        self.list_files_m.assert_not_called()
        self.log_m.assert_called_once_with("Excluding entry %r", "<name>")

    def test_single_file(self):
        entry = BackupEntry("<name>", "single-file", "/home/file.pdf", "<folder-id>")
        self.get_settings_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"

        _main()

        self.backup_m.assert_called_once_with(
            "/home/file.pdf", "<mimetype>", "<folder-id>"
        )
        self.get_mt_m.assert_called_once_with("/home/file.pdf")
        self.get_settings_m.assert_called_once_with()
        self.list_files_m.assert_not_called()
        self.log_m.assert_not_called()

    @pytest.mark.parametrize("nulls", range(11))
    def test_single_file_mix(self, nulls):
        entry1 = BackupEntry("<name>", "single-file", "/home/file.pdf", "<folder-id>")
        entry2 = BackupEntry("<name>", "single-file", None, "<folder-id>")
        entries = [entry1] * (10 - nulls) + [entry2] * nulls
        random.shuffle(entries)

        self.get_settings_m.return_value = entries
        self.get_mt_m.return_value = "<mimetype>"

        _main()

        self.get_settings_m.assert_called_once_with()
        self.list_files_m.assert_not_called()

        if nulls != 10:
            self.backup_m.assert_called_with(
                "/home/file.pdf", "<mimetype>", "<folder-id>"
            )
            self.get_mt_m.assert_called_with("/home/file.pdf")
        else:
            self.backup_m.assert_not_called()
            self.get_mt_m.assert_not_called()

        if nulls != 0:
            self.log_m.assert_called_with("Excluding entry %r", "<name>")

        self.bytesio_m.assert_not_called()
        assert self.backup_m.call_count == 10 - nulls
        assert self.get_mt_m.call_count == 10 - nulls
        assert self.log_m.call_count == nulls

    def test_invalid_type(self):
        entry = BackupEntry("<name>", "single-file", None, "<folder-id>")
        entry = mock.MagicMock(
            **{
                "name": "<name>",
                "type": "<invalid-type>",
                "root-folder": "<root-folder>",
            }
        )
        self.get_settings_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"

        with pytest.raises(SettingsError, match="Invalid EntryType: '<invalid-type>'"):
            _main()

        self.backup_m.assert_not_called()
        self.bytesio_m.assert_not_called()
        self.get_mt_m.assert_not_called()
        self.get_settings_m.assert_called_once_with()
        self.list_files_m.assert_not_called()

    @pytest.mark.parametrize("use_zip", [True, False])
    def test_multiple_no_files_found(self, use_zip):
        entry = BackupEntry(
            "<name>",
            "multiple-files",
            "/home/test",
            "<folder-id>",
            zip=use_zip,
            filter="<filter>",
        )
        self.get_settings_m.return_value = [entry]
        self.list_files_m.return_value = []

        with pytest.raises(
            NoFilesFoundError, match="No files found for entry '<name>'"
        ):
            _main()

        self.backup_m.assert_not_called()
        self.get_mt_m.assert_not_called()
        self.get_settings_m.assert_called_once_with()
        self.list_files_m.assert_called_once_with("/home/test", "<filter>")
        self.zipfile_m.assert_not_called()
        self.bytesio_m.assert_not_called()

    @pytest.mark.parametrize("zipname", ["myzip.zip", None])
    def test_multiple_zip(self, zipname):
        entry = BackupEntry(
            "<name>",
            "multiple-files",
            "/home/test",
            "<folder-id>",
            zip=True,
            zipname=zipname,
        )
        self.get_settings_m.return_value = [entry]
        self.list_files_m.return_value = [
            "/home/test/doc.pdf",
            "/home/test/proyect/doc.pdf",
            "/home/test/proyect/specs.pdf",
            "/home/test/trash/unused/delete.py",
        ]

        _main()

        zipfile_m = self.zipfile_m.return_value.__enter__.return_value
        for file in self.list_files_m.return_value:
            arcname = file.replace("/home/test/", "")
            zipfile_m.write.assert_any_call(file, arcname=arcname)

        self.backup_m.assert_called_once_with(
            self.bytesio_m.return_value, ZIP_MIMETYPE, "<folder-id>", filename=zipname
        )

        self.bytesio_m.assert_called_once_with()
        self.get_mt_m.assert_not_called()
        self.get_settings_m.assert_called_once_with()
        self.list_files_m.called_once_with()

    def test_multiple_no_zip(self):
        entry = BackupEntry(
            "<name>", "multiple-files", "/home/test", "<folder-id>", zip=False
        )
        self.get_settings_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"
        self.list_files_m.return_value = [
            "/home/test/doc.pdf",
            "/home/test/proyect/doc.pdf",
            "/home/test/proyect/specs.pdf",
            "/home/test/trash/unused/delete.py",
        ]

        _main()

        assert self.backup_m.call_count == 4
        assert self.get_mt_m.call_count == 4

        for file in self.list_files_m.return_value:
            self.backup_m.assert_any_call(file, "<mimetype>", "<folder-id>")
            self.get_mt_m.assert_any_call(file)

        self.bytesio_m.assert_not_called()
        self.get_settings_m.assert_called_once_with()
        self.list_files_m.called_once_with()


class TestMain:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.hid_main_m = mock.patch("backup_to_cloud.main._main").start()
        self.list_files_m = mock.patch("backup_to_cloud.main.list_files").start()
        self.parse_args_m = mock.patch("backup_to_cloud.main.parse_args").start()

        yield

        mock.patch.stopall()

    def test_fail(self):
        self.parse_args_m.side_effect = SystemExit

        with pytest.raises(SystemExit):
            main()

        self.hid_main_m.assert_not_called()
        self.list_files_m.assert_not_called()
        self.parse_args_m.assert_called_once_with()

    def test_check_regex(self, capsys):
        namespace = Namespace(
            **{"command": "check-regex", "root-path": "<root-path>", "regex": "<regex>"}
        )
        self.parse_args_m.return_value = namespace

        m = mock.MagicMock()
        m.__str__.return_value = "<file>"
        self.list_files_m.return_value = [m] * 20

        with pytest.raises(SystemExit, match="0"):
            main()

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == "<file>\n" * 20

        m.__str__.assert_called()
        assert m.__str__.call_count == 20

        self.parse_args_m.assert_called_once_with()
        self.list_files_m.assert_called_once_with("<root-path>", "<regex>")
        self.hid_main_m.assert_not_called()

    def test_normal_execution(self):
        self.parse_args_m.return_value = Namespace(command=None)

        main()

        self.hid_main_m.assert_called_once_with()
        self.parse_args_m.assert_called_once_with()
        self.list_files_m.assert_not_called()


class TestParseArgs:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.sys_argv_m = mock.patch("sys.argv").start()
        yield
        mock.patch.stopall()

    def set_args(self, args):
        real_args = ["test.py"] + shlex.split(args)
        self.sys_argv_m.__getitem__.side_effect = lambda s: real_args[s]

    def parse_args(self):
        try:
            args = parse_args()
            return args
        finally:
            self.sys_argv_m.__getitem__.assert_called_once_with(slice(1, None, None))

    def test_none(self):
        self.set_args("")
        args = self.parse_args()
        assert vars(args) == {"command": None}

    def test_check_regex_ok(self):
        self.set_args("check-regex '/path/to/root test/' .regex$")
        args = self.parse_args()
        assert vars(args) == {
            "command": "check-regex",
            "root-path": "/path/to/root test/",
            "regex": ".regex$",
        }

    def test_check_regex_ok_no_regex(self):
        self.set_args("check-regex '/path/to/root test/'")
        args = self.parse_args()
        assert vars(args) == {
            "command": "check-regex",
            "root-path": "/path/to/root test/",
            "regex": ".",
        }

    def test_check_regex_fail_no_path(self, capsys):
        self.set_args("check-regex")

        with pytest.raises(SystemExit):
            self.parse_args()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "usage" in captured.err
        assert "error: the following arguments are required: root-path" in captured.err
