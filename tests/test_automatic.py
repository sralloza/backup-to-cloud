from itertools import permutations
from unittest import mock

import pytest

from backup_to_cloud.automatic import (
    ATTRS_TYPES,
    REQUIRED_ATTRS,
    BackupEntry,
    EntryType,
    check_yaml_entry,
    get_automatic_entries,
)
from backup_to_cloud.exceptions import AutomaticEntryError


class TestBackupEntry:
    def test_init_min(self):
        entry = BackupEntry("<name>", "single-file", "<root-path>")
        assert entry.name == "<name>"
        assert entry.type == EntryType.single_file
        assert entry.root_path == "<root-path>"
        assert entry.folder == "root"
        assert entry.zip is False
        assert entry.zipname is None
        assert entry.filter == "."

    def test_init_all(self):
        entry = BackupEntry(
            "<name>",
            "multiple-files",
            "<root-path>",
            "<cloud-folder-id>",
            True,
            "<zipname>",
            "<filter>",
        )
        assert entry.name == "<name>"
        assert entry.type == EntryType.multiple_files
        assert entry.root_path == "<root-path>"
        assert entry.folder == "<cloud-folder-id>"
        assert entry.zip is True
        assert entry.zipname == "<zipname>"
        assert entry.filter == "<filter>"

    def test_init_type_error(self):
        with pytest.raises(ValueError, match="'invalid-type' is not a valid EntryType"):
            BackupEntry("<name>", "invalid-type", "<root-path>")

    def test_repr(self):
        entry = BackupEntry("<name>", "single-file", "<root-path>")
        attrs = vars(entry)
        assert repr(entry) == "BackupEntry(attrs=%s)" % attrs


class TestGetAuto:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.settings_m = mock.patch("backup_to_cloud.automatic.settings").start()
        self.check_m = mock.patch("backup_to_cloud.automatic.check_yaml_entry").start()
        self.be_m = mock.patch("backup_to_cloud.automatic.BackupEntry").start()
        yield
        mock.patch.stopall()

    def test_get_auto(self):
        self.check_m.return_value = {"a": 1, "b": 2, "c": 3}
        self.settings_m.automatic_path.read_text.return_value = (
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

        auto = get_automatic_entries()

        self.check_m.assert_any_call(**dict1)
        self.check_m.assert_any_call(**dict2)
        self.be_m.assert_any_call(a=1, b=2, c=3)
        self.be_m.assert_any_call(a=1, b=2, c=3)

        assert auto == [self.be_m.return_value] * 2


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

    def test_invalid_attrs(self, attrs):
        attrs["invalid"] = True
        with pytest.raises(
            AutomaticEntryError, match=r"'invalid' is not a valid attribute"
        ):
            check_yaml_entry(**attrs)

    @pytest.mark.parametrize("missing", REQUIRED_ATTRS)
    def test_missing_attrs(self, attrs, missing):
        name = "null" if missing == "name" else "name"
        msg = f"Missing required attributes in query {name}: {set([missing])!r}"
        del attrs[missing.replace("_", "-")]
        with pytest.raises(AutomaticEntryError, match=msg):
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
        with pytest.raises(AutomaticEntryError, match=msg):
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

        with pytest.raises(AutomaticEntryError, match="Must provide 'zipname'"):
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
        for attr in ATTRS_TYPES:
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
