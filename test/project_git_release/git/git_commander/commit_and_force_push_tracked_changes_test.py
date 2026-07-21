import subprocess
from unittest.mock import MagicMock, call

from conftest import __DEFAULT_GIT_STDOUT, __DEFAULT_GIT_STDERR, __DEFAULT_GIT_EXIT_CODE


def commit_and_force_push_side_effect(commit: bool = True,
                                      push: bool = True):
    def side_effect(*args, **kwargs):

        if args[0][1] == "commit" and not commit:
            raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")
        if args[0][1] == "push" and not push:
            raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")

        proc_mock = MagicMock(spec=subprocess.CompletedProcess)
        proc_mock.stdout = __DEFAULT_GIT_STDOUT
        proc_mock.stderr = __DEFAULT_GIT_STDERR
        proc_mock.returncode = __DEFAULT_GIT_EXIT_CODE
        return proc_mock

    return side_effect


def test_commit_and_force_push_commit_error(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    next_full_version = "0.1.0"
    expected_command = ["git", "commit", "-m",
                        release_config.release_commit_message.replace("%VERSION%", next_full_version)]
    subp_mock.side_effect = commit_and_force_push_side_effect(commit=False)

    result = commander.commit_and_force_push_tracked_changes(next_full_version)
    assert not result

    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call("Error while commiting files")


def test_commit_and_force_push_error(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    next_full_version = "0.1.0"
    expected_command = ["git", "push", "--porcelain", "--force", "origin", release_config.release_branch]
    subp_mock.side_effect = commit_and_force_push_side_effect(push=False)

    result = commander.commit_and_force_push_tracked_changes(next_full_version)
    assert not result

    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call("Error while force pushing changes")


def test_commit_and_force_push(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    next_full_version = "0.1.0"
    expected_command = ["git", "push", "--porcelain", "--force", "origin", release_config.release_branch]
    subp_mock.side_effect = commit_and_force_push_side_effect()

    result = commander.commit_and_force_push_tracked_changes(next_full_version)
    assert result

    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    for error_msg in ["Error while commiting files", "Error while force pushing changes"]:
        assert call(error_msg) not in log_error_spy.mock_calls
