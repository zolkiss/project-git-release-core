import pytest
from pytest_mock import MockType

from project_git_release import log
from project_git_release.core import ReleaseConfig

__TEST_TOKEN_VALUE = "VERY_TOKEN_VALUE"
__TEST_REPO_URL = "http://localhost:8080"
__TEST_REPO_OWNER = "owner"
__TEST_REPO_NAME = "repository"
__TEST_DEFAULT_BRANCH = "main"
__TEST_FULL_URL = f"{__TEST_REPO_URL}/{__TEST_REPO_OWNER}/{__TEST_REPO_NAME}"


@pytest.fixture
def release_config():
    return ReleaseConfig(
        token=__TEST_TOKEN_VALUE,
        url=__TEST_REPO_URL,
        owner=__TEST_REPO_OWNER,
        repo=__TEST_REPO_NAME,
        default_branch=__TEST_DEFAULT_BRANCH
    )


@pytest.fixture
def log_info_spy(mocker) -> MockType:
    return mocker.spy(log, 'info')


@pytest.fixture
def log_warn_spy(mocker) -> MockType:
    return mocker.spy(log, 'warning')


@pytest.fixture
def log_debug_spy(mocker) -> MockType:
    return mocker.spy(log, 'debug')


@pytest.fixture
def log_error_spy(mocker) -> MockType:
    return mocker.spy(log, 'error')
