# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- New files were uploaded to the `root` folder regardless of setting `cloud-folder-id`.

## [2.0.0] - 2020-06-20

### Added

- Add attribute `filter`.
- Improve MIME type detection.
- Add CLI command `gen-token` to generate a new token from the credentials file (`credentials.json`)

### Changed

- Default `cloud-folder-id` is now `root`, which corresponds to the root folder of google drive.
- Improved naming of files inside the zip file.
- Rename attribute `path` to `root-path`.
- Rename entry types: `folder` → `multiple-files`, `file` → `single-file`.

### Fixed

- Added tests for everything.
- Fixed [README](README.md)
- Fixed bugs.

## [1.0.0] - 2020-06-16

### Added

- Initial release

[unreleased]: https://github.com/sralloza/backup-to-cloud/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/sralloza/backup-to-cloud/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/sralloza/backup-to-cloud/releases/tag/v1.0.0
