from enum import Enum
from itertools import permutations
from unittest import mock

import pytest
from ruamel.yaml import YAML

from backup_to_cloud.exceptions import SettingsError
from backup_to_cloud.settings import (
    ATTRS_TYPES,
    BackupEntry,
    EntryType,
    REQUIRED_ATTRS,
    SettingsError,
    check_yaml_entry,
    get_settings,
)


class TestBackupEntry:
    def test_init_min(self):
        be = BackupEntry("<name>", "single-file", "<root-path>")
        assert be.name == "<name>"
        assert be.type == EntryType.single_file
        assert be.root_path == "<root-path>"
        assert be.folder is None
        assert be.zip is False
        assert be.zipname is None
        assert be.filter == "."

    def test_init_all(self):
        be = BackupEntry(
            "<name>",
            "multiple-files",
            "<root-path>",
            "<cloud-folder-id>",
            True,
            "<zipname>",
            "<filter>",
        )
        assert be.name == "<name>"
        assert be.type == EntryType.multiple_files
        assert be.root_path == "<root-path>"
        assert be.folder == "<cloud-folder-id>"
        assert be.zip is True
        assert be.zipname == "<zipname>"
        assert be.filter == "<filter>"

    def test_init_type_error(self):
        with pytest.raises(ValueError, match="'invalid-type' is not a valid EntryType"):
            BackupEntry("<name>", "invalid-type", "<root-path>")

    def test_repr(self):
        be = BackupEntry("<name>", "single-file", "<root-path>")
        attrs = vars(be)
        assert repr(be) == "BackupEntry(attrs=%s)" % attrs


class TestGetSettings:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.set_path_m = mock.patch("backup_to_cloud.settings.SETTINGS_PATH").start()
        self.check_m = mock.patch("backup_to_cloud.settings.check_yaml_entry").start()
        self.be_m = mock.patch("backup_to_cloud.settings.BackupEntry").start()
        yield
        mock.patch.stopall()

    def test_get_settings(self):
        self.check_m.return_value = {"a": 1, "b": 2, "c": 3}
        self.set_path_m.read_text.return_value = (
            "name1:\n  type: <type1>\n  zip: true\n  root-path: <path1>\n  "
            "zipname: <zipname1>\n  cloud-folder-id: <folder-id1>\n  filter:"
            " .\n\nname2:\n  type: <type2>\n  zip: false\n  root-path: "
            "<path2>\n  zipname: <zipname2>\n  cloud-folder-id: <folder-id2>\n "
            ' filter: "*.pdf"\n'
        )
        dict1 = {
            "name": "name1",
            "type": "<type1>",
            "zip": True,
            "root-path": "<path1>",
            "zipname": "<zipname1>",
            "cloud-folder-id": "<folder-id1>",
            "filter": ".",
        }

        dict2 = {
            "name": "name2",
            "type": "<type2>",
            "zip": False,
            "root-path": "<path2>",
            "zipname": "<zipname2>",
            "cloud-folder-id": "<folder-id2>",
            "filter": "*.pdf",
        }

        settings = get_settings()

        self.check_m.assert_any_call(**dict1)
        self.check_m.assert_any_call(**dict2)
        self.be_m.assert_any_call(a=1, b=2, c=3)
        self.be_m.assert_any_call(a=1, b=2, c=3)

        assert settings == [self.be_m.return_value] * 2


class TestCheckYamlEntry:
    @pytest.fixture
    def attrs(self):
        """Basic attributes of BackupEntry."""
        attrs = {"name": "name", "root-path": "/home/test", "type": "single-file"}
        yield attrs

    def test_ok_basic(self, attrs):
        result = check_yaml_entry(**attrs)
        assert result == {
            "name": "name",
            "root_path": "/home/test",
            "type": "single-file",
        }

    # def test_error_no_name(self, attrs):
    #     attrs.pop("name")
    #     with pytest.raises(TypeError, match=r"check_yaml_entry\(\) [\s\w]+: 'name'"):
    #         check_yaml_entry(**attrs)

    def test_invalid_attrs(self, attrs):
        attrs["invalid"] = True
        with pytest.raises(SettingsError, match=r"'invalid' is not a valid attribute"):
            check_yaml_entry(**attrs)

    @pytest.mark.parametrize("missing", REQUIRED_ATTRS)
    def test_missing_attrs(self, attrs, missing):
        name = "null" if missing == "name" else "name"
        msg = f"Missing required attributes in query {name}: {set([missing])!r}"
        del attrs[missing.replace("_", "-")]
        with pytest.raises(SettingsError, match=msg):
            check_yaml_entry(**attrs)

    @pytest.mark.parametrize("missing", permutations(REQUIRED_ATTRS))
    def test_missing_multiple_attrs(self, attrs, missing):
        set_missing = list(permutations(missing))
        set_missing = [
            "{" + "%s" % ", ".join(repr(k) for k in x) + "}" for x in set_missing
        ]
        name = "null" if "name" in missing else "name"
        set_missing = f"({'|'.join(set_missing)})"
        msg = f"Missing required attributes in query {name}: {set_missing}"

        for key in missing:
            del attrs[key.replace("_", "-")]
        with pytest.raises(SettingsError, match=msg):
            check_yaml_entry(**attrs)

    def test_ok_zipped_folder(self):
        attrs = {
            "name": "name",
            "root-path": "/home/test",
            "type": "multiple-files",
            "zip": True,
            "zipname": "a.zip",
        }
        result = check_yaml_entry(**attrs)
        assert result == {
            "name": "name",
            "root_path": "/home/test",
            "type": "multiple-files",
            "zip": True,
            "zipname": "a.zip",
        }

    def test_error_zipped_folder(self):
        attrs = {
            "name": "name",
            "root-path": "/home/test",
            "type": "multiple-files",
            "zip": True,
        }

        with pytest.raises(SettingsError, match="Must provide 'zipname'"):
            check_yaml_entry(**attrs)

    def test_ok_unzipped_folder(self):
        attrs = {
            "name": "name",
            "root-path": "/home/test",
            "type": "multiple-files",
            "zip": False,
            "zipname": "a.zip",
        }
        result = check_yaml_entry(**attrs)
        assert result == {
            "name": "name",
            "root_path": "/home/test",
            "type": "multiple-files",
            "zip": False,
            "zipname": "a.zip",
        }

    def test_invalid_entry_type(self, attrs):
        attrs["type"] = "invalid-type"
        with pytest.raises(TypeError, match="'invalid-type' is not a valid Entrytype"):
            check_yaml_entry(**attrs)

    @pytest.mark.parametrize("attribute", ATTRS_TYPES.keys() - {"type"})
    def test_invalid_types(self, attrs, attribute):
        for attr in ATTRS_TYPES.keys():
            if attr == attribute:
                continue
            if attr in attrs:
                continue
            attrs[attr] = ATTRS_TYPES[attr](2)
        attrs[attribute] = 1 + 2j

        match = (
            f"{attribute!r} must be {ATTRS_TYPES[attribute].__name__!r}, not 'complex'"
        )
        if attribute not in REQUIRED_ATTRS:
            match = "If defined, " + match
        with pytest.raises(TypeError, match=match):
            check_yaml_entry(**attrs)
