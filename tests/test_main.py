from argparse import Namespace
import shlex
from unittest import mock

import pytest

from backup_to_cloud.main import main, parse_args


@pytest.mark.skip
def test_hidden_main():
    assert 0, "Not implemented"


class TestMain:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.hid_main_m = mock.patch("backup_to_cloud.main._main").start()
        self.list_files_m = mock.patch("backup_to_cloud.main.list_files").start()
        self.parse_args_m = mock.patch("backup_to_cloud.main.parse_args").start()

        yield

        mock.patch.stopall()

    def test_fail(self):
        self.parse_args_m.side_effect = SystemExit

        with pytest.raises(SystemExit):
            main()

        self.hid_main_m.assert_not_called()
        self.list_files_m.assert_not_called()
        self.parse_args_m.assert_called_once_with()

    def test_check_regex(self, capsys):
        namespace = Namespace(
            **{"command": "check-regex", "root-path": "<root-path>", "regex": "<regex>"}
        )
        self.parse_args_m.return_value = namespace

        m = mock.MagicMock()
        m.__str__.return_value = "<file>"
        self.list_files_m.return_value = [m] * 20

        with pytest.raises(SystemExit, match="0"):
            main()

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == "<file>\n" * 20

        m.__str__.assert_called()
        assert m.__str__.call_count == 20

        self.parse_args_m.assert_called_once_with()
        self.list_files_m.assert_called_once_with("<root-path>", "<regex>")
        self.hid_main_m.assert_not_called()

    def test_normal_execution(self):
        self.parse_args_m.return_value = Namespace(command=None)

        main()

        self.hid_main_m.assert_called_once_with()
        self.parse_args_m.assert_called_once_with()
        self.list_files_m.assert_not_called()


class TestParseArgs:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.sys_argv_m = mock.patch("sys.argv").start()
        yield
        mock.patch.stopall()

    def set_args(self, args):
        real_args = ["test.py"] + shlex.split(args)
        self.sys_argv_m.__getitem__.side_effect = lambda s: real_args[s]

    def parse_args(self):
        try:
            args = parse_args()
            return args
        finally:
            self.sys_argv_m.__getitem__.assert_called_once_with(slice(1, None, None))

    def test_none(self):
        self.set_args("")
        args = self.parse_args()
        assert vars(args) == {"command": None}

    def test_check_regex_ok(self):
        self.set_args("check-regex '/path/to/root test/' .regex$")
        args = self.parse_args()
        assert vars(args) == {
            "command": "check-regex",
            "root-path": "/path/to/root test/",
            "regex": ".regex$",
        }

    def test_check_regex_ok_no_regex(self):
        self.set_args("check-regex '/path/to/root test/'")
        args = self.parse_args()
        assert vars(args) == {
            "command": "check-regex",
            "root-path": "/path/to/root test/",
            "regex": ".",
        }

    def test_check_regex_fail_no_path(self, capsys):
        self.set_args("check-regex")

        with pytest.raises(SystemExit):
            self.parse_args()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "usage" in captured.err
        assert "error: the following arguments are required: root-path" in captured.err
