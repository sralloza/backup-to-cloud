"""
backup_to_cloud
---------------

Designed to manage automatic backups to Google Drive.

Should be used with a task manager, such as Cron.

"""
from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
