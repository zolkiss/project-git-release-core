from tempfile import TemporaryDirectory

from project_git_release import log
from project_git_release.classes import NewVersion
from project_git_release.core.release_config import ReleaseConfig


def generate_version_file(temp_dir: TemporaryDirectory, config: ReleaseConfig, new_version: NewVersion):
    if config.version_file is None:
        return

    version_file = f"{temp_dir.name}/{config.version_file}"
    log.info("Creating version_file: %s", version_file)
    with open(version_file, "w+") as f:
        f.write(new_version.get_full_version())
