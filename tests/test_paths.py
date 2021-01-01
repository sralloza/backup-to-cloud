from pathlib import Path

from backup_to_cloud.paths import (
    CREDENTIALS_PATH,
    LOG_PATH,
    ROOT_PATH,
    AUTOMATIC_PATH,
    TOKEN_PATH,
)


def test_root_path():
    assert isinstance(ROOT_PATH, Path)
    assert ROOT_PATH.joinpath("README.md").exists()
    assert ROOT_PATH.exists()
    assert ROOT_PATH.suffix == ""
    assert ROOT_PATH.is_dir()


def test_credentials_path():
    assert isinstance(CREDENTIALS_PATH, Path)
    assert CREDENTIALS_PATH.relative_to(ROOT_PATH) == Path(CREDENTIALS_PATH.name)
    assert CREDENTIALS_PATH.suffix == ".json"


def test_log_path():
    assert isinstance(LOG_PATH, Path)
    assert LOG_PATH.relative_to(ROOT_PATH) == Path(LOG_PATH.name)
    assert LOG_PATH.suffix == ".log"


def test_settings_path():
    assert isinstance(AUTOMATIC_PATH, Path)
    assert AUTOMATIC_PATH.relative_to(ROOT_PATH) == Path(AUTOMATIC_PATH.name)
    assert AUTOMATIC_PATH.suffix == ".yml"


def test_token_path():
    assert isinstance(TOKEN_PATH, Path)
    assert TOKEN_PATH.relative_to(ROOT_PATH) == Path(TOKEN_PATH.name)
    assert TOKEN_PATH.suffix == ".pickle"
