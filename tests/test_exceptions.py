import pytest

from backup_to_cloud.exceptions import (
    AutomaticEntryError,
    BackupError,
    MultipleFilesError,
    NoFilesFoundError,
    TokenError,
)


class TestBackupError:
    def test_inheritance(self):
        exc = BackupError()
        assert isinstance(exc, BackupError)
        assert isinstance(exc, Exception)

    def test_raises(self):
        with pytest.raises(BackupError):
            raise BackupError


class TestMultipleFilesError:
    def test_inheritance(self):
        exc = MultipleFilesError()
        assert isinstance(exc, MultipleFilesError)
        assert isinstance(exc, BackupError)

    def test_raises(self):
        with pytest.raises(MultipleFilesError):
            raise MultipleFilesError


class TestNoFilesFoundError:
    def test_inheritance(self):
        exc = NoFilesFoundError()
        assert isinstance(exc, NoFilesFoundError)
        assert isinstance(exc, BackupError)

    def test_raises(self):
        with pytest.raises(NoFilesFoundError):
            raise NoFilesFoundError


class TestAutomaticEntryError:
    def test_inheritance(self):
        exc = AutomaticEntryError()
        assert isinstance(exc, AutomaticEntryError)
        assert isinstance(exc, BackupError)

    def test_raises(self):
        with pytest.raises(AutomaticEntryError):
            raise AutomaticEntryError


class TestTokenError:
    def test_inheritance(self):
        exc = TokenError()
        assert isinstance(exc, TokenError)
        assert isinstance(exc, BackupError)

    def test_raises(self):
        with pytest.raises(TokenError):
            raise TokenError
