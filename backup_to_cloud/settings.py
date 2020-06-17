from enum import Enum
from typing import Dict

from ruamel.yaml import YAML

from .paths import SETTINGS_PATH
from .utils import log


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
            name (str): the name of the entry. It is irrelevant, only representative.
            type (str): the entry type. Right now it can be `single-file` or
                `multiple-files`.
            root_path (str): if type is `single-file`, it represents the path of the
                file. If type is `multiple-files`, it represents the root folder where
                the sistem will start listing files.
            filter (str): if the type is `multiple-files`, this regex filter will
                be applied to every file located below `root-path`. The search it's
                recursively. For example, to select all pdf files, use `filter=.py`.
                By default is `'.'`, which is a regex for match anything. It is
                encouraged to check the regex before creating the first backup.
                To check the regex check README). Defaults to '.'.
            cloud_folder_id (str, optional): id of the folder to save the file(s)
                into. If is not present or is None, the files will be stored in
                the root folder (`Drive`). Defaults to None.
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
    def fmt(kw: Dict[str, str]) -> Dict[str, str]:
        return {k.replace("-", "_"): v for k, v in kw.items()}

    settings_dict = YAML(typ="safe").load(SETTINGS_PATH.read_text())
    try:
        return [BackupEntry(name=k, **fmt(v)) for k, v in settings_dict.items()]
    except TypeError as exc:
        log(str(exc))
        raise exc
