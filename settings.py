from enum import Enum

from ruamel.yaml import YAML


class EntryType(Enum):
    multiple_files = "multiple-files"
    singple_file = "single-file"


class BackupEntry:
    def __init__(self, name, type, path, cloud_folder_id=None, zip=False, zipname=None):
        self.name = name
        self.type = EntryType(type)
        self.path = path
        self.folder = cloud_folder_id
        self.zip = zip
        self.zipname = zipname

    def __repr__(self):
        return vars(self).__repr__()


def get_settings(settings_path):
    settings_dict = YAML(typ="safe").load(settings_path.read_text())
    try:
        return [BackupEntry(name=k, **v) for k, v in settings_dict.items()]
    except TypeError as exc:
        from start import log

        log(str(exc))
        raise exc
