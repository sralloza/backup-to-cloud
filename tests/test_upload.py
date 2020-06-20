from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest

from backup_to_cloud.exceptions import MultipleFilesError
from backup_to_cloud.upload import backup, save_new_file, save_version


class TestBackup:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.p_exists_m = mock.patch("pathlib.Path.exists").start()
        self.p_read_bytes_m = mock.patch("pathlib.Path.read_bytes").start()
        self.sgds_m = mock.patch(
            "backup_to_cloud.upload.get_google_drive_services"
        ).start()
        self.bytesio_m = mock.patch("backup_to_cloud.upload.BytesIO").start()
        self.new_ver_m = mock.patch("backup_to_cloud.upload.save_version").start()
        self.new_file_m = mock.patch("backup_to_cloud.upload.save_new_file").start()
        self.log_m = mock.patch("backup_to_cloud.upload.log").start()

        yield

        mock.patch.stopall()

    _file_data = {
        "Path": Path("<filepath>"),
        "str": "<filepath>",
        "BytesIO": BytesIO(b"<filedata>"),
    }

    @pytest.fixture(params=[None, 0, 1, 2])
    def nids(self, request):
        yield request.param

    @pytest.fixture(params=[True, False])
    def exists(self, request):
        yield request.param

    @pytest.fixture(params=["<filename>", None])
    def filename(self, request):
        yield request.param

    @pytest.fixture(params=["Path", "str", "BytesIO"])
    def file_data(self, request):
        yield self._file_data[request.param]

    def test_backup(self, exists, file_data, filename, nids):
        self.p_exists_m.return_value = exists
        useful_filename = filename or "<filepath>"

        files = self.sgds_m.return_value.files.return_value
        id_m = mock.MagicMock()
        id_m.get.side_effect = range(10)
        response = {}
        if nids is None:
            nids = 0
        else:
            response["files"] = [id_m] * nids
        files.list.return_value.execute.return_value = response

        mimetype = None
        result = None
        folder_id = "<folder-id>"

        # Manage file_data different types
        if not exists and not isinstance(file_data, BytesIO):
            with pytest.raises(FileNotFoundError, match="<filepath>") as exc:
                backup(file_data, mimetype, folder_id, filename)

            self.p_exists_m.assert_called_once_with()
            self.p_read_bytes_m.assert_not_called()
            self.bytesio_m.assert_not_called()

            self.sgds_m.assert_not_called()
            self.log_m.assert_called_once_with(exc.value)
            return

        if isinstance(file_data, BytesIO) and not filename:
            msg = "If file_data is BytesIO, filename is required"
            with pytest.raises(ValueError, match=msg) as exc:
                backup(file_data, mimetype, folder_id, filename)

            self.p_exists_m.assert_not_called()
            self.p_read_bytes_m.assert_not_called()
            self.bytesio_m.assert_not_called()

            self.sgds_m.assert_not_called()
            self.log_m.assert_called_once_with(exc.value)
            return

        if nids > 1:
            msg = "Detected more than one file named '%s' in the target folder"
            with pytest.raises(MultipleFilesError, match=msg % useful_filename) as exc:
                backup(file_data, mimetype, folder_id, filename)

            self.log_m.assert_called_once_with(exc.value)

            if isinstance(file_data, BytesIO):
                self.p_exists_m.assert_not_called()
            else:
                self.p_exists_m.assert_called_once_with()
                self.bytesio_m.assert_called_once_with(self.p_read_bytes_m.return_value)

        if nids <= 1:
            result = backup(file_data, mimetype, folder_id, filename)

        if isinstance(file_data, BytesIO):
            self.p_exists_m.assert_not_called()
        else:
            self.p_exists_m.assert_called_once_with()
            self.bytesio_m.assert_called_once_with(self.p_read_bytes_m.return_value)

        # Google Drive API
        self.sgds_m.assert_called_once_with()
        query = "name = '%s' and '<folder-id>' in parents" % useful_filename

        self.sgds_m.return_value.files.assert_called_once_with()
        files.list.assert_called_once_with(q=query, fields="files(id, name)")
        files.list.return_value.execute.assert_called_once_with()

        assert id_m.get.call_count == nids

        if nids > 1:
            return

        self.log_m.assert_not_called()

        if isinstance(file_data, BytesIO):
            shipped_data = file_data
        else:
            shipped_data = self.bytesio_m.return_value

        if nids == 0:
            self.new_file_m.assert_called_once_with(
                self.sgds_m.return_value,
                shipped_data,
                mimetype,
                folder_id,
                useful_filename,
            )
            self.new_ver_m.assert_not_called()
            assert result == self.new_file_m.return_value
        if nids == 1:
            self.new_file_m.assert_not_called()
            self.new_ver_m.assert_called_once_with(
                self.sgds_m.return_value, shipped_data, mimetype, 0, useful_filename
            )
            assert result == self.new_ver_m.return_value


@mock.patch("backup_to_cloud.upload.log")
@mock.patch("backup_to_cloud.upload.MediaIoBaseUpload")
def test_save_new_file(mibu_m, log_m):
    gds = mock.MagicMock()
    buffer = BytesIO(b"<file-data>")

    result = save_new_file(gds, buffer, "<mimetype>", "<folder-id>", "<filename>")

    log_m.assert_called_with("Saving new file: %s", "<filename>")

    metadata = {
        "name": "<filename>",
        "mimeType": "<mimetype>",
        "parents": "<folder-id>",
    }
    mibu_m.assert_called_once_with(buffer, mimetype="<mimetype>")
    gds.files.assert_called_once_with()

    files = gds.files.return_value
    files.create.assert_called_once_with(
        body=metadata, media_body=mibu_m.return_value, fields="id"
    )
    command = files.create.return_value
    command.execute.assert_called_once_with()

    assert result == command.execute.return_value


@mock.patch("backup_to_cloud.upload.log")
@mock.patch("backup_to_cloud.upload.MediaIoBaseUpload")
def test_save_version(mibu_m, log_m):
    gds = mock.MagicMock()
    buffer = BytesIO(b"<file-data>")

    result = save_version(gds, buffer, "<mimetype>", "<file-id>", "<filename>")

    log_m.assert_called_with("Saving new version of %s", "<filename>")

    mibu_m.assert_called_once_with(buffer, mimetype="<mimetype>")
    gds.files.assert_called_once_with()

    files = gds.files.return_value
    files.update.assert_called_once_with(
        fileId="<file-id>", keepRevisionForever=False, media_body=mibu_m.return_value
    )
    command = files.update.return_value
    command.execute.assert_called_once_with()

    assert result == command.execute.return_value
