from subprocess import CompletedProcess
from unittest.mock import MagicMock

import pytest

from project_git_release.git import GitCommander

__DEFAULT_GIT_STDOUT = "The command returned..."
__DEFAULT_GIT_STDERR = "The program errored with..."
__DEFAULT_GIT_EXIT_CODE = 0

__TEST_TEMP_DIR = "test_tmp"


@pytest.fixture
def subp_mock(mocker):
    proc_mock = MagicMock(spec=CompletedProcess)
    proc_mock.stdout = __DEFAULT_GIT_STDOUT
    proc_mock.stderr = __DEFAULT_GIT_STDERR
    proc_mock.returncode = __DEFAULT_GIT_EXIT_CODE

    patch = mocker.patch("subprocess.run")
    patch.return_value = proc_mock

    return patch


@pytest.fixture
def commander(release_config):
    return GitCommander(release_config, __TEST_TEMP_DIR)


def setup_git_mock(subp_mock,
                   stdout: str = __DEFAULT_GIT_STDOUT,
                   stderr: str = __DEFAULT_GIT_STDERR,
                   return_code: int = __DEFAULT_GIT_EXIT_CODE):
    proc_mock = MagicMock(spec=CompletedProcess)
    proc_mock.stdout = stdout
    proc_mock.stderr = stderr
    proc_mock.returncode = return_code

    subp_mock.return_value = proc_mock
