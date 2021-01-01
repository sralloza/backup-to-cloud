import random
from unittest import mock

import pytest

from backup_to_cloud.exceptions import NoFilesFoundError, AutomaticEntryError
from backup_to_cloud.main import create_backup
from backup_to_cloud.automatic import BackupEntry
from backup_to_cloud.utils import ZIP_MIMETYPE


class TestCreateBackup:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.backup_m = mock.patch("backup_to_cloud.main.backup").start()
        self.get_mt_m = mock.patch("backup_to_cloud.main.get_mimetype").start()
        self.get_autentr_m = mock.patch("backup_to_cloud.main.get_automatic_entries").start()
        self.list_files_m = mock.patch("backup_to_cloud.main.list_files").start()
        self.zipfile_m = mock.patch("backup_to_cloud.main.ZipFile").start()
        self.bytesio_m = mock.patch("backup_to_cloud.main.BytesIO").start()
        self.log_m = mock.patch("backup_to_cloud.main.log").start()

        yield

        mock.patch.stopall()

    def test_no_root_path(self):
        entry = BackupEntry("<name>", "single-file", None, "<folder-id>")
        self.get_autentr_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"

        create_backup()

        self.backup_m.assert_not_called()
        self.get_mt_m.assert_not_called()
        self.get_autentr_m.assert_called_once_with()
        self.list_files_m.assert_not_called()
        self.log_m.assert_called_once_with("Excluding entry %r", "<name>")

    def test_single_file(self):
        entry = BackupEntry("<name>", "single-file", "/home/file.pdf", "<folder-id>")
        self.get_autentr_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"

        create_backup()

        self.backup_m.assert_called_once_with(
            "/home/file.pdf", "<mimetype>", "<folder-id>"
        )
        self.get_mt_m.assert_called_once_with("/home/file.pdf")
        self.get_autentr_m.assert_called_once_with()
        self.list_files_m.assert_not_called()
        self.log_m.assert_not_called()

    @pytest.mark.parametrize("nulls", range(11))
    def test_single_file_mix(self, nulls):
        entry1 = BackupEntry("<name>", "single-file", "/home/file.pdf", "<folder-id>")
        entry2 = BackupEntry("<name>", "single-file", None, "<folder-id>")
        entries = [entry1] * (10 - nulls) + [entry2] * nulls
        random.shuffle(entries)

        self.get_autentr_m.return_value = entries
        self.get_mt_m.return_value = "<mimetype>"

        create_backup()

        self.get_autentr_m.assert_called_once_with()
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
        self.get_autentr_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"

        with pytest.raises(
            AutomaticEntryError, match="Invalid EntryType: '<invalid-type>'"
        ):
            create_backup()

        self.backup_m.assert_not_called()
        self.bytesio_m.assert_not_called()
        self.get_mt_m.assert_not_called()
        self.get_autentr_m.assert_called_once_with()
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
        self.get_autentr_m.return_value = [entry]
        self.list_files_m.return_value = []

        with pytest.raises(
            NoFilesFoundError, match="No files found for entry '<name>'"
        ):
            create_backup()

        self.backup_m.assert_not_called()
        self.get_mt_m.assert_not_called()
        self.get_autentr_m.assert_called_once_with()
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
        self.get_autentr_m.return_value = [entry]
        self.list_files_m.return_value = [
            "/home/test/doc.pdf",
            "/home/test/proyect/doc.pdf",
            "/home/test/proyect/specs.pdf",
            "/home/test/trash/unused/delete.py",
        ]

        create_backup()

        zipfile_m = self.zipfile_m.return_value.__enter__.return_value
        for file in self.list_files_m.return_value:
            arcname = file.replace("/home/test/", "")
            zipfile_m.write.assert_any_call(file, arcname=arcname)

        self.backup_m.assert_called_once_with(
            self.bytesio_m.return_value, ZIP_MIMETYPE, "<folder-id>", filename=zipname
        )

        self.bytesio_m.assert_called_once_with()
        self.get_mt_m.assert_not_called()
        self.get_autentr_m.assert_called_once_with()
        self.list_files_m.called_once_with()

    def test_multiple_no_zip(self):
        entry = BackupEntry(
            "<name>", "multiple-files", "/home/test", "<folder-id>", zip=False
        )
        self.get_autentr_m.return_value = [entry]
        self.get_mt_m.return_value = "<mimetype>"
        self.list_files_m.return_value = [
            "/home/test/doc.pdf",
            "/home/test/proyect/doc.pdf",
            "/home/test/proyect/specs.pdf",
            "/home/test/trash/unused/delete.py",
        ]

        create_backup()

        assert self.backup_m.call_count == 4
        assert self.get_mt_m.call_count == 4

        for file in self.list_files_m.return_value:
            self.backup_m.assert_any_call(file, "<mimetype>", "<folder-id>")
            self.get_mt_m.assert_any_call(file)

        self.bytesio_m.assert_not_called()
        self.get_autentr_m.assert_called_once_with()
        self.list_files_m.called_once_with()
