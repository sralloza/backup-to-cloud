from setuptools import find_packages, setup
import versioneer

setup(
    name="backup-to-cloud",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
)
