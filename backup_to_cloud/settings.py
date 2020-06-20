"""Handles the settings and the settings file (.settings.yml)."""

from enum import Enum
from typing import Dict, List

from ruamel.yaml import YAML

from .exceptions import SettingsError
from .paths import SETTINGS_PATH


class EntryType(Enum):
    """Valid types for BackupEntry."""

    multiple_files = "multiple-files"
    single_file = "single-file"


REQUIRED_ATTRS = {"name", "type", "root_path"}
VALID_TYPES = {x.value for x in EntryType}
ATTRS_TYPES = {
    "name": str,
    "type": str,
    "root_path": str,
    "cloud_folder_id": str,
    "zip": bool,
    "zipname": str,
    "filter": str,
}
VALID_ATTRS = set(ATTRS_TYPES.keys())


class BackupEntry:
    """Represents an entry in .settings.yml

    Args:
        name (str): the name of the entry. It is irrelevant, only representative.
        type (str): the entry type. Right now it can be `single-file` or
            `multiple-files`.
        root_path (str): if type is `single-file`, it represents the path of the
            file. If type is `multiple-files`, it represents the root folder where
            the sistem will start listing files.
        cloud_folder_id (str, optional): id of the folder to save the file(s)
            into. If is not present or is 'root', the files will be stored in
            the root folder (`Drive`). Defaults to 'root'.
        zip (bool, optional): If True and type is folder, all files will be uploaded as
            zip. Defaults to False.
        zipname (str, optional): if zip, this is the file name. Defaults to None.
        filter (str): if the type is `multiple-files`, this regex filter will
            be applied to every file located below `root-path`. The search it's
            recursively. For example, to select all pdf files, use `filter=.py`.
            By default is `'.'`, which is a regex for match anything. It is
            encouraged to check the regex before creating the first backup.
            To check the regex check README). Defaults to '.'.
    """

    def __init__(
        self,
        name,
        type,
        root_path,
        cloud_folder_id="root",
        zip=False,
        zipname=None,
        filter=".",
    ):

        self.name = name
        self.type = EntryType(type)
        self.root_path = root_path
        self.folder = cloud_folder_id
        self.zip = zip
        self.zipname = zipname
        self.filter = filter

    def __repr__(self):
        attrs = vars(self).__repr__()
        return f"BackupEntry(attrs={attrs})"


def get_settings() -> List[BackupEntry]:
    """Parses the settings file and returns a list of BackupEntries.

    Returns:
        List[BackupEntry]: backup entries parsed.
    """

    settings_dict = YAML(typ="safe").load(SETTINGS_PATH.read_text())

    entries = []
    for name, yaml_entry in settings_dict.items():
        result = check_yaml_entry(name=name, **yaml_entry)
        entries.append(BackupEntry(**result))
    return entries


def check_yaml_entry(**yaml_entry: Dict[str, str]) -> Dict[str, str]:
    """Checks the validity of the attributes of a backup entry.

    Args:
        **yaml_entry (Dict[str, str]): attributes of the yaml entry
            that needs to be parsed.

    Raises:
        SettingsError: if any attribute is not defined.
        SettingsError: if a required attribute is not defined.
        TypeError: if the entry type is invalid.
        TypeError: if any attribute it's not the type it should be.
        SettingsError: if entry type is multiple-files, zip is True
            and zipname is not defiend.

    Returns:
        Dict[str, str]: attributes parsed.
    """

    result = {}
    keys = set()
    for key, value in yaml_entry.items():
        key = key.replace("-", "_")
        if key not in VALID_ATTRS:
            msg = f"{key!r} is not a valid attribute {VALID_ATTRS}"
            raise SettingsError(msg)

        result[key] = value
        keys.add(key)

    if REQUIRED_ATTRS - keys:
        missing = REQUIRED_ATTRS - keys
        name = result.get("name", "null")
        msg = f"Missing required attributes in query {name}: {missing!r}"
        raise SettingsError(msg)

    if result["type"] not in VALID_TYPES:
        valid_types = ", ".join(VALID_TYPES)
        msg = f"{result['type']!r} is not a valid Entrytype ({valid_types})"
        raise TypeError(msg)

    def check_attr(key, required):
        attr_type = ATTRS_TYPES[key]

        if result.get(key) or required:
            if not isinstance(result[key], attr_type):
                real_type = type(result.get(key)).__name__
                msg = ""
                if not required:
                    msg += "If defined, "
                msg += f"{key!r} must be {attr_type.__name__!r}, not {real_type!r}"

                raise TypeError(msg)

    for attribute in VALID_ATTRS - REQUIRED_ATTRS:
        check_attr(attribute, False)

    for attribute in REQUIRED_ATTRS:
        check_attr(attribute, True)

    if result.get("zip"):
        if not result.get("zipname"):
            raise SettingsError("Must provide 'zipname' if zip=True")

    return result
