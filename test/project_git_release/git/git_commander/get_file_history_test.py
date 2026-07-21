import subprocess

import pytest

from conftest import setup_git_mock
from project_git_release.classes import ShortCommitData
from project_git_release.git.git_commander import COMMIT_SEPARATOR


def test_get_file_history_errors(subp_mock, commander, release_config, log_error_spy,
                                 log_debug_spy):
    expected_command = ["git", "log", f"origin/{release_config.default_branch}"]
    path = "temp_path.txt"
    subp_mock.side_effect = subprocess.CalledProcessError(1, ' '.join(expected_command), "", "")

    with pytest.raises(SystemExit) as sys_ext_wrapper:
        commander.get_file_history(path, False)

    assert sys_ext_wrapper.type == SystemExit
    assert sys_ext_wrapper.value.code == 1

    log_error_spy.assert_any_call(f"Error while getting commits for {path} on {release_config.default_branch}")


def test_get_file_history(subp_mock, commander, release_config, log_error_spy,
                          log_debug_spy):
    path = "temp_path.txt"
    expected_command = ["git", "log", f"origin/{release_config.default_branch}", f"--pretty=%H{COMMIT_SEPARATOR}%s",
                        "--", f"{path}"]
    setup_git_mock(subp_mock=subp_mock, stdout="hash_one|Commit Message One\nhash_two|Commit Message Two")

    result = commander.get_file_history(path, False)

    assert result is not None
    assert result[0] == ShortCommitData("Commit Message One", "hash_one")
    assert result[1] == ShortCommitData("Commit Message Two", "hash_two")
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))


def test_get_file_history_reverse(subp_mock, commander, release_config, log_error_spy,
                                  log_debug_spy):
    path = "temp_path.txt"
    expected_command = ["git", "log", f"origin/{release_config.default_branch}", "--reverse",
                        f"--pretty=%H{COMMIT_SEPARATOR}%s", "--", f"{path}"]
    setup_git_mock(subp_mock=subp_mock, stdout="hash_one|Commit Message One\nhash_two|Commit Message Two")

    result = commander.get_file_history(path, True)

    assert result is not None
    assert result[0] == ShortCommitData("Commit Message One", "hash_one")
    assert result[1] == ShortCommitData("Commit Message Two", "hash_two")
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))


def test_get_file_history_invalid_commit_format(subp_mock, commander, release_config, log_warn_spy,
                                                log_debug_spy):
    path = "temp_path.txt"
    expected_command = ["git", "log", f"origin/{release_config.default_branch}", f"--pretty=%H{COMMIT_SEPARATOR}%s",
                        "--", f"{path}"]
    setup_git_mock(subp_mock=subp_mock,
                   stdout="hash_one|Commit Message One\nhash_two but invalid stuff Commit Message Two")

    result = commander.get_file_history(path, False)

    assert result is not None
    assert 1 == len(result)
    assert result[0] == ShortCommitData("Commit Message One", "hash_one")
    log_warn_spy.assert_any_call(f"Cannot split commit line 'hash_two but invalid stuff Commit Message Two'")
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
