import sys
from datetime import datetime
from pathlib import Path


class ChangelogEditor:
    def __init__(self):
        self.lines = Path("CHANGELOG.md").read_text("utf8").splitlines()
        self.current_release = self.find_current_version()

    def release(self, new_version):
        self.fix_links(new_version)
        self.fix_header(new_version)

    def fix_header(self, new_version):
        for i, line in enumerate(self.lines):
            if "[Unreleased]" in line and "##" in line:
                today_str = datetime.now().strftime("%Y-%m-%d")
                self.lines.insert(i + 1, f"## [{new_version}] - {today_str}")
                self.lines.insert(i + 1, "")
                return

    def fix_links(self, new_version):
        for i, line in enumerate(self.lines):
            if "[unreleased]" in line and "#" not in line:
                self.lines[i] = line.replace(self.current_release, new_version)
                new_link = "https://github.com/BelinguoAG/full-power-backend/compare/v{}...v{}".format(
                    self.current_release, new_version
                )
                new_link = f"[{new_version}]: {new_link}"
                self.lines.insert(i + 1, new_link)
                return

    def find_current_version(self):
        for line in self.lines:
            if "[unreleased]" in line and "#" not in line:
                return line.split("/")[-1].split("...")[0][1:]
        raise Exception

    def write(self):
        Path("CHANGELOG.md").write_text("\n".join(self.lines) + "\n", "utf8")


changelog = ChangelogEditor()
changelog.release(sys.argv[1])
changelog.write()
