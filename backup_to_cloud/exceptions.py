class BackupError(Exception):
    pass


class MultipleFilesError(BackupError):
    pass


class NoFilesFoundError(BackupError):
    pass


class SettingsError(BackupError):
    pass


class TokenError(BackupError):
    pass
