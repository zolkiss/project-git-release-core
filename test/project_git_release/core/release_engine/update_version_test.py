import datetime
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest

from project_git_release import ReleaseEngine, Connector
from project_git_release.classes import GitHashAndMsg, CommitDetails, ShortCommitData, GitRelease, NewVersion
from project_git_release.common.changelog_generator import ChangelogGenerator
from project_git_release.git import GitCommander
from project_git_release.test_classes import DummyConnector

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


def test_no_latest_release_and_no_new_commit(engine_mock, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(return_value=None)

    with pytest.raises(SystemExit) as se:
        engine_mock.engine.update_version()
        assert 0 == se.value.code

    log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")


def test_no_latest_release_and_no_new_commit_error(engine_mock, log_error_spy):
    engine_mock.connector.get_latest_release = MagicMock(return_value=None)
    engine_mock.git_commander.get_commits_since_latest_release.return_value = None

    with pytest.raises(SystemExit) as se:
        engine_mock.engine.update_version()
        assert 1 == se.value.code

    log_error_spy.assert_any_call("Error while getting commits since last release...")


def test_no_latest_release_and_has_no_valid_commits(engine_mock, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(return_value=None)
    engine_mock.git_commander.get_file_history.return_value = [
        ShortCommitData(message="New Commit 01", sha="sha_01"),
        ShortCommitData(message="New Commit 02", sha="sha_02")
    ]

    with pytest.raises(SystemExit) as se:
        engine_mock.engine.update_version()
        assert 0 == se.value.code

    log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")


def test_first_release_no_commit_after(engine_mock, release_config, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(return_value=None)
    engine_mock.git_commander.get_file_history.return_value = [
        ShortCommitData(message="feat: New feature", sha="sha_01"),
        ShortCommitData(message="chore: Release version 0.1.0", sha="sha_02")
    ]

    with pytest.raises(SystemExit) as se:
        engine_mock.engine.update_version()
        assert 0 == se.value.code

    log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")


def commit_details_se(hash_and_message: GitHashAndMsg) -> CommitDetails:
    return CommitDetails(hash=hash_and_message.hash, title=hash_and_message.message,
                         creation_time=datetime.datetime.fromisocalendar(2025, 1, 1), body=None, footers=[])


def test_first_release_has_commit_after(mocker, engine_mock, release_config, log_info_spy):
    mocker.patch.object(engine_mock.connector, "get_latest_release", return_value=MagicMock(return_value=None))
    engine_mock.git_commander.get_file_history.return_value = [
        ShortCommitData(message="chore: Release version 0.1.0", sha="sha_02")
    ]
    engine_mock.git_commander.get_commits_since_latest_release.return_value = [
        GitHashAndMsg(message="feat: New Feature One", hash="sha_01"),
        GitHashAndMsg(message="fix: New Fix One", hash="sha_02"),
        GitHashAndMsg(message="test: Test", hash="sha_03"),
        GitHashAndMsg(message="chore!: Very Breaking change", hash="sha_04")
    ]
    mocker.patch.object(engine_mock.connector, "get_commit_details", side_effect=commit_details_se)

    engine_mock.engine.update_version()

    assert NewVersion("1.0.0", release_config.release_version_prefix) == engine_mock.next_version_spy.spy_return

    with pytest.raises(AssertionError):
        log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")


def test_second_release_has_commit_after(mocker, engine_mock, release_config, log_info_spy):
    mocker.patch.object(engine_mock.connector, "get_latest_release",
                        return_value=GitRelease("0.0.1", "chore: Release version 0.0.1", "sha_00"))
    engine_mock.git_commander.get_file_history.return_value = [
        ShortCommitData(message="chore: Release version 0.1.0", sha="sha_02"),
        ShortCommitData(message="chore: Release version 0.0.1", sha="sha_00")
    ]
    engine_mock.git_commander.get_commits_since_latest_release.return_value = [
        GitHashAndMsg(message="feat: New Feature One", hash="sha_01"),
        GitHashAndMsg(message="fix: New Fix One", hash="sha_02"),
        GitHashAndMsg(message="test: Test", hash="sha_03"),
        GitHashAndMsg(message="chore!: Very Breaking change", hash="sha_04")
    ]
    mocker.patch.object(engine_mock.connector, "get_commit_details", side_effect=commit_details_se)

    engine_mock.engine.update_version()

    assert NewVersion("1.0.0", release_config.release_version_prefix) == engine_mock.next_version_spy.spy_return

    with pytest.raises(AssertionError):
        log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")


def test_first_release_has_only_bugfix(mocker, engine_mock, release_config, log_info_spy):
    mocker.patch.object(engine_mock.connector, "get_latest_release", return_value=MagicMock(return_value=None))
    engine_mock.git_commander.get_file_history.return_value = [
        ShortCommitData(message="chore: Release version 0.1.0", sha="sha_02")
    ]
    engine_mock.git_commander.get_commits_since_latest_release.return_value = [
        GitHashAndMsg(message="fix: New Fix One", hash="sha_02")
    ]
    mocker.patch.object(engine_mock.connector, "get_commit_details", side_effect=commit_details_se)

    engine_mock.engine.update_version()

    assert NewVersion("0.1.1", release_config.release_version_prefix) == engine_mock.next_version_spy.spy_return

    with pytest.raises(AssertionError):
        log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")
