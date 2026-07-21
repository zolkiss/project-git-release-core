import datetime
from unittest.mock import MagicMock

import pytest

from project_git_release.classes import GitRelease, ShortCommitData, GitHashAndMsg, CommitDetails, GitReleaseResponse


def test_no_unreleased_pr(engine_mock, log_info_spy):
    engine_mock.engine.release_unreleased_prs()
    log_info_spy.assert_any_call("Cannot find unreleased merged PR")


def test_has_latest_release_no_new_release(engine_mock, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(
        return_value=GitRelease("0.0.1", "chore: Release version 0.0.1", "sha_00"))
    engine_mock.git_commander.get_file_history = MagicMock(return_value=[
        ShortCommitData("chore: Release version 0.0.1", "sha_00")
    ])

    engine_mock.engine.release_unreleased_prs()
    log_info_spy.assert_any_call("Cannot find unreleased merged PR")


def test_has_latest_release_has_new_release(engine_mock, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(
        return_value=GitRelease("0.0.1", "chore: Release version 0.0.1", "sha_00"))
    engine_mock.git_commander.get_file_history = MagicMock(return_value=[
        ShortCommitData("chore: Release version 0.1.0", "sha_01"),
        ShortCommitData("chore: Release version 0.0.1", "sha_00")
    ])

    with pytest.raises(SystemExit) as se:
        engine_mock.engine.release_unreleased_prs()
        assert 0 == se.value.code

    log_info_spy.assert_any_call("Unreleased chore PR: %s ('%s', %s)", "0.1.0", "chore: Release version 0.1.0",
                                 "sha_01")


def test_has_latest_release_has_new_release_but_no_commit(engine_mock, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(
        return_value=GitRelease("0.0.1", "chore: Release version 0.0.1", "sha_00"))
    engine_mock.git_commander.get_file_history = MagicMock(return_value=[
        ShortCommitData("chore: Release version 0.1.0", "sha_01"),
        ShortCommitData("chore: Release version 0.0.1", "sha_00")
    ])

    with pytest.raises(SystemExit) as se:
        engine_mock.engine.release_unreleased_prs()
        assert 0 == se.value.code

    log_info_spy.assert_any_call("Unreleased chore PR: %s ('%s', %s)", "0.1.0", "chore: Release version 0.1.0",
                                 "sha_01")
    log_info_spy.assert_any_call("There is no commit since the latest release. Quitting...")


def test_has_latest_release_has_new_release_with_commits(engine_mock, log_info_spy):
    engine_mock.connector.get_latest_release = MagicMock(
        return_value=GitRelease("0.0.1", "chore: Release version 0.0.1", "sha_00"))

    feature_sha = "sha_01"
    feature_message = "feat: Very Feature 01"

    engine_mock.git_commander.get_file_history = MagicMock(return_value=[
        ShortCommitData("chore: Release version 0.1.0", "sha_02"),
        ShortCommitData(feature_message, feature_sha),
        ShortCommitData("chore: Release version 0.0.1", "sha_00")
    ])

    engine_mock.git_commander.get_commits_since_latest_release = MagicMock(return_value=[
        GitHashAndMsg(feature_message, feature_sha)
    ])
    engine_mock.connector.get_commit_details = MagicMock(
        return_value=CommitDetails(feature_sha, feature_message, datetime.datetime.fromisocalendar(2025, 1, 1),
                                   None, []))

    expected_response = GitReleaseResponse("0.1.0", "chore: Release version 0.1.0", "sha_02", 1, False, False)
    engine_mock.connector.create_release = MagicMock(return_value=expected_response)

    engine_mock.engine.release_unreleased_prs()

    log_info_spy.assert_any_call("Unreleased chore PR: %s ('%s', %s)", "0.1.0", "chore: Release version 0.1.0",
                                 "sha_02")
    log_info_spy.assert_any_call("Release is created with response:\n%s", expected_response)
