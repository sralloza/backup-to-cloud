import argparse
from enum import Enum

from ruamel.yaml import YAML

from paths import SETTINGS_PATH
from utils import log


class EntryType(Enum):
    multiple_files = "multiple-files"
    single_file = "single-file"


class BackupEntry:
    def __init__(
        self,
        name,
        type,
        root_path,
        cloud_folder_id=None,
        zip=False,
        zipname=None,
        filter=".",
    ):
        """Represents an entry in .settings.yml

        Args:
            name (str): name of the entry.
            type (str): type of the entry. Must be declared as EntryType.
            path (str): path of the entry. Can be glob.
            cloud_folder_id (str, optional): Id of the folder to save in google drvie.
                If None, the files will be uploaded to the root folder. Defaults to None.
            zip (bool, optional): If True and type is folder, all files will be uploaded as
                zip. Defaults to False.
            zipname (str, optional): if zip, this is the file name. Defaults to None.
        """

        self.name = name
        self.type = EntryType(type)
        self.root_path = root_path
        self.folder = cloud_folder_id
        self.zip = zip
        self.zipname = zipname
        self.filter = filter

    def __repr__(self):
        return vars(self).__repr__()


def get_settings():
    settings_dict = YAML(typ="safe").load(SETTINGS_PATH.read_text())
    try:
        return [BackupEntry(name=k, **v) for k, v in settings_dict.items()]
    except TypeError as exc:
        log(str(exc))
        raise exc


def parse_args():
    parser = argparse.ArgumentParser("backup-to-cloud")
    subparsers = parser.add_subparsers()
    check_glob_parser = subparsers.add_parser("check-glob")
