from enum import Enum
from pathlib import Path

from ruamel.yaml import YAML


class EntryType(Enum):
    folder = "d"
    file = "-"


class BackupEntry:
    def __init__(self, name, type, path, cloud_folder_id=None, zip=False):
        self.name = name
        self.type = EntryType[type]
        self.path = path
        self.folder = cloud_folder_id
        self.zip = zip

    def __repr__(self):
        return vars(self).__repr__()


def get_settings(settings_path):
    settings_dict = YAML(typ="safe").load(settings_path.read_text())
    return [BackupEntry(name=k, **v) for k, v in settings_dict.items()]
