from enum import Enum

from ruamel.yaml import YAML

from .paths import SETTINGS_PATH
from .utils import log


class EntryType(Enum):
    multiple_files = "multiple-files"
    single_file = "single-file"


VALID_ATTRS = ["name", "type", "root_path", "folder", "zip", "zipname", "filter"]
REQUIRED_ATTRS = {"name", "type", "root_path"}
VALID_TYPES = {"multiple-files", "single-file"}


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
    settings_dict = YAML(typ="safe").load(SETTINGS_PATH.read_text())

    entries = []
    for name, yaml_entry in settings_dict.items():
        result = check_yaml_entry(name=name, **yaml_entry)
        entries.append(BackupEntry(name=name, **result))
    return entries


def check_yaml_entry(name, **yaml_entry):
    result = {}
    keys = set(["name"])
    for key, value in yaml_entry.items():
        key = key.replace("-", "_")
        if key not in VALID_ATTRS:
            raise Exception

        result[key] = value
        keys.add(key)

    if REQUIRED_ATTRS - keys:
        missing = REQUIRED_ATTRS - keys
        msg = f"Missing required attributes in query {name}: {missing!r}"
        raise Exception(msg)

    if result["type"] not in VALID_TYPES:
        msg = f"{result['type']!r} if not a valid type {VALID_TYPES}"
        raise TypeError(msg)

    def check_attr(key, attr_type):
        if result.get(key):
            if not isinstance(result[key], attr_type):
                real_type = type(attr_type).__name__
                msg = f"If defined, {key} must be {attr_type}, not {real_type}"
                exc = TypeError(msg)
                log(str(exc))
                raise exc

    check_attr("cloud_folder_id", str)
    check_attr("zip", bool)
    check_attr("zipname", str)
    check_attr("filter", str)

    return result
