from tempfile import TemporaryDirectory

from pgr import log
from pgr.classes import NewVersion
from pgr.core.release_config import ReleaseConfig


def generate_version_file(temp_dir: TemporaryDirectory, config: ReleaseConfig, new_version: NewVersion):
    if config.version_file is None:
        return

    version_file = f"{temp_dir.name}/{config.version_file}"
    log.info("Creating version_file: %s", version_file)
    with open(version_file, "w+") as f:
        f.write(new_version.get_full_version())
