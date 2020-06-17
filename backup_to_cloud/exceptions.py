class BackupError(Exception):
    pass


class TokenError(BackupError):
    pass


class SettingsError(BackupError):
    pass
