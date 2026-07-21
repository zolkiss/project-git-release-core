from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest
from test_classes import DummyConnector

from project_git_release import ReleaseEngine, Connector
from project_git_release.common.changelog_generator import ChangelogGenerator
from project_git_release.git import GitCommander

_DEFAULT_TEMP_DIR_NAME = "//temp/dir"


@pytest.fixture
def connector(release_config) -> DummyConnector:
    return DummyConnector(release_config)


@pytest.fixture
def git_commander() -> MagicMock:
    mock = MagicMock(spec=GitCommander)
    mock.get_file_history.return_value = []
    mock.is_release_branch_exists.return_value = False
    mock.create_release_branch.return_value = True
    mock.update_release_branch.return_value = True
    mock.clone_repository.return_value = True
    mock.add_untracked_files.return_value = True
    mock.commit_and_force_push_tracked_changes.return_value = True
    mock.get_commits_since_latest_release.return_value = []
    return mock


@pytest.fixture
def temp_dir() -> MagicMock:
    temp_dir = MagicMock(spec=TemporaryDirectory)
    temp_dir.name = _DEFAULT_TEMP_DIR_NAME
    return temp_dir


@pytest.fixture
def changelog_generator(mocker) -> MagicMock:
    mock = MagicMock(spec=ChangelogGenerator)
    mocker.patch.object(ChangelogGenerator, "__new__", return_value=mock)
    return mock


@pytest.fixture
def gen_version_file(mocker) -> MagicMock:
    return mocker.patch("project_git_release.core.release_engine.generate_version_file")


class ReleaseEngineMocks:
    def __init__(self, engine: ReleaseEngine, git_commander: GitCommander, temp_dir: TemporaryDirectory,
                 changelog_generator: ChangelogGenerator, connector: Connector, next_version_spy: MagicMock):
        self.engine = engine
        self.git_commander = git_commander
        self.temp_dir = temp_dir
        self.changelog_generator = changelog_generator
        self.connector = connector
        self.next_version_spy = next_version_spy


@pytest.fixture
def engine_mock(mocker, connector, git_commander, temp_dir, release_config, changelog_generator,
                gen_version_file) -> ReleaseEngineMocks:
    engine = ReleaseEngine(connector=connector, git_commander=git_commander, temp_dir=temp_dir, config=release_config)
    return ReleaseEngineMocks(
        engine=engine,
        git_commander=git_commander,
        temp_dir=temp_dir,
        changelog_generator=changelog_generator,
        connector=connector,
        next_version_spy=mocker.spy(engine, "_ReleaseEngine__calculate_next_version")
    )
