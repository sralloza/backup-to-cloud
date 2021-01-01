from setuptools import find_packages, setup
import versioneer
from pathlib import Path

requirements = Path("requirements.txt").read_text().splitlines()


setup(
    name="backup-to-cloud",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "backup-to-cloud=backup_to_cloud.cli:main",
            "btc=backup_to_cloud.cli:main",
        ],
    },
    install_requires=requirements
)
