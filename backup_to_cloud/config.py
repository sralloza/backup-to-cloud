"""Module to define imporant file paths."""

from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, validator
from pydantic.types import DirectoryPath, FilePath


class Settings(BaseSettings):
    """Base settings of the application."""
    
    root_path: DirectoryPath
    credentials_path: Optional[FilePath]

    @validator("credentials_path", pre=True)
    def check_credentials_path(cls, v, values):
        if not v and "root_path" in values:
            return values["root_path"].joinpath("credentials.json")

        return v

    @validator("credentials_path")
    def check_credentials_path_exists(cls, v):
        if v:
            return FilePath.validate(v)

    @property
    def log_path(self) -> Path:
        return self.root_path.joinpath("cloud-backup.log")

    @property
    def automatic_path(self) -> Path:
        return self.root_path.joinpath(".automatic.yml")

    @property
    def token_path(self) -> Path:
        return self.root_path.joinpath("token.pickle")

    class Config:
        env_prefix = "btc_"
        validate_assignment = True


settings = Settings()
