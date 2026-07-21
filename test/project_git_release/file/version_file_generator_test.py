from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, mock_open, patch

from project_git_release.classes import NewVersion
from project_git_release.file import generate_version_file


def test_generate_version_file_no_version_file(release_config):
    temp_dir_mock = MagicMock(spec=TemporaryDirectory)
    release_config.version_file = None

    generate_version_file(temp_dir_mock, release_config, NewVersion("0.0.1", ""))


def test_generate_version_file(release_config):
    temp_dir_mock = MagicMock(spec=TemporaryDirectory)
    temp_dir_mock.name = "not_valid_path"

    mo = mock_open()
    with patch("builtins.open", mo):
        generate_version_file(temp_dir_mock, release_config, NewVersion("0.0.1", ""))
        mo.assert_called_once_with(f"{temp_dir_mock.name}/{release_config.version_file}", "w+")
        mo().write.assert_called_once_with("0.0.1")
