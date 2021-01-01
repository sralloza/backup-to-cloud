import os
from pathlib import Path

import pytest
from backup_to_cloud.config import Settings, settings
from pydantic import ValidationError
from pydantic.types import DirectoryPath, FilePath


def test_settings_fields():
    fields = Settings.__fields__
    assert set(fields) == {"root_path", "credentials_path"}

    assert fields["root_path"].required is True
    assert fields["credentials_path"].required is False
    assert fields["root_path"].type_ == DirectoryPath
    assert fields["credentials_path"].type_ == FilePath


def test_root_path():
    environ_var = os.environ["BTC_ROOT_PATH"]

    del os.environ["BTC_ROOT_PATH"]
    with pytest.raises(ValidationError, match="value_error.missing"):
        Settings()

    os.environ["BTC_ROOT_PATH"] = "C:/invalid-path"
    with pytest.raises(
        ValidationError, match="invalid-path.+value_error.path.not_exists"
    ):
        Settings()

    os.environ["BTC_ROOT_PATH"] = Path(__file__).parent.as_posix()
    with pytest.raises(
        ValidationError, match="credentials.json.+value_error.path.not_exists"
    ):
        Settings()

    os.environ["BTC_ROOT_PATH"] = environ_var


def test_credentials_path():
    assert isinstance(settings.credentials_path, Path)
    assert settings.credentials_path.relative_to(settings.root_path) == Path(
        settings.credentials_path.name
    )
    assert settings.credentials_path.suffix == ".json"


def test_log_path():
    assert isinstance(settings.log_path, Path)
    assert settings.log_path.relative_to(settings.root_path) == Path(
        settings.log_path.name
    )
    assert settings.log_path.suffix == ".log"


def test_settings_path():
    assert isinstance(settings.automatic_path, Path)
    assert settings.automatic_path.relative_to(settings.root_path) == Path(
        settings.automatic_path.name
    )
    assert settings.automatic_path.suffix == ".yml"


def test_token_path():
    assert isinstance(settings.token_path, Path)
    assert settings.token_path.relative_to(settings.root_path) == Path(
        settings.token_path.name
    )
    assert settings.token_path.suffix == ".pickle"
