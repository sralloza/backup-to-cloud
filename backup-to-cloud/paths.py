from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent
CREDENTIALS_PATH = ROOT_PATH.joinpath("credentials.json")
LOG_PATH = ROOT_PATH.joinpath("cloud-backup.log")
SETTINGS_PATH = ROOT_PATH.joinpath(".settings.yml")
TOKEN_PATH = ROOT_PATH.joinpath("token.pickle")
