import subprocess

from conftest import setup_git_mock
from project_git_release.git.git_commander import COMMIT_SEPARATOR


def test_get_commits_since_latest_release_no_prev_version_errors(subp_mock, commander, release_config, log_error_spy,
                                                                 log_debug_spy):
    default_branch_ref = f"origin/{release_config.default_branch}"
    expected_command = ["git", "log", default_branch_ref, "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s"]
    subp_mock.side_effect = subprocess.CalledProcessError(1, ' '.join(expected_command), "", "")
    result = commander.get_commits_since_latest_release(None, None)

    assert not result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call(f"Error while getting commits for {default_branch_ref}")


def test_get_commits_since_latest_release_no_prev_version(subp_mock, commander, release_config, log_error_spy,
                                                          log_debug_spy):
    default_branch_ref = f"origin/{release_config.default_branch}"
    expected_command = ["git", "log", default_branch_ref, "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s"]
    setup_git_mock(subp_mock=subp_mock, stdout="hash_one|Commit Message One\nhash_two|Commit Message Two")

    result = commander.get_commits_since_latest_release(None, None)

    assert result is not None
    assert 2 == len(result)

    first_result = result[0]
    assert "hash_one" == first_result.hash
    assert "Commit Message One" == first_result.message
    second_result = result[1]
    assert "hash_two" == second_result.hash
    assert "Commit Message Two" == second_result.message
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))


def test_get_commits_since_latest_release_has_prev_version_errors(subp_mock, commander, release_config, log_error_spy,
                                                                  log_debug_spy):
    latest_release_commit = "latest_release_commit"
    default_branch_ref = f"origin/{release_config.default_branch}"
    expected_command = ["git", "log", "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s",
                        f"{latest_release_commit}..{default_branch_ref}"]

    subp_mock.side_effect = subprocess.CalledProcessError(1, ' '.join(expected_command), "", "")
    result = commander.get_commits_since_latest_release(latest_release_commit, None)

    assert not result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call(f"Error while getting commits for {default_branch_ref}")


def test_get_commits_since_latest_release_between_commits_errors(subp_mock, commander, release_config, log_error_spy,
                                                                 log_debug_spy):
    latest_release_commit = "latest_release_commit"
    until_commit = "until_commit"
    default_branch_ref = f"origin/{release_config.default_branch}"
    expected_command = ["git", "log", "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s",
                        f"{latest_release_commit}..{until_commit}"]

    subp_mock.side_effect = subprocess.CalledProcessError(1, ' '.join(expected_command), "", "")
    result = commander.get_commits_since_latest_release(latest_release_commit, until_commit)

    assert not result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call(f"Error while getting commits for {default_branch_ref}")


def test_get_commits_since_latest_release_has_prev_version(subp_mock, commander, release_config, log_error_spy,
                                                           log_debug_spy):
    latest_release_commit = "latest_release_commit"
    default_branch_ref = f"origin/{release_config.default_branch}"
    expected_command = ["git", "log", "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s",
                        f"{latest_release_commit}..{default_branch_ref}"]

    setup_git_mock(subp_mock=subp_mock, stdout="hash_one|Commit Message One\nhash_two|Commit Message Two")

    result = commander.get_commits_since_latest_release(latest_release_commit, None)

    assert result is not None
    assert 2 == len(result)

    first_result = result[0]
    assert "hash_one" == first_result.hash
    assert "Commit Message One" == first_result.message
    second_result = result[1]
    assert "hash_two" == second_result.hash
    assert "Commit Message Two" == second_result.message
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))


def test_get_commits_since_latest_release_between_commits(subp_mock, commander, release_config, log_error_spy,
                                                          log_debug_spy):
    latest_release_commit = "latest_release_commit"
    until_commit = "until_commit"
    default_branch_ref = f"origin/{release_config.default_branch}"
    expected_command = ["git", "log", "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s",
                        f"{latest_release_commit}..{until_commit}"]

    setup_git_mock(subp_mock=subp_mock, stdout="hash_one|Commit Message One\nhash_two|Commit Message Two")

    result = commander.get_commits_since_latest_release(latest_release_commit, until_commit)

    assert result is not None
    assert 2 == len(result)

    first_result = result[0]
    assert "hash_one" == first_result.hash
    assert "Commit Message One" == first_result.message
    second_result = result[1]
    assert "hash_two" == second_result.hash
    assert "Commit Message Two" == second_result.message
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
