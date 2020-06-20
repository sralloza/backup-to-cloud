"""Exceptions used in `backup_to_cloud`."""


class BackupError(Exception):
    """Base class for exceptions in the app."""


class MultipleFilesError(BackupError):
    """There is more than one file in the target folder named as
    the target file.
    """


class NoFilesFoundError(BackupError):
    """No files found for a BackupEntry, given the path and filter."""


class SettingsError(BackupError):
    """Maluse of settings."""


class TokenError(BackupError):
    """Errors related to the google drive token."""
