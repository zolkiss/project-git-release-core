import subprocess
from unittest.mock import MagicMock, call

from conftest import __DEFAULT_GIT_STDOUT, __DEFAULT_GIT_STDERR, __DEFAULT_GIT_EXIT_CODE


def update_release_side_effect(fetch: bool = True, checkout: bool = True, reset: bool = True):
    def side_effect(*args, **kwargs):
        cmd = args[0][1]
        if cmd == "fetch" and not fetch:
            raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")
        if cmd == "checkout" and not checkout:
            raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")
        if cmd == "reset" and not reset:
            raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")

        proc_mock = MagicMock(spec=subprocess.CompletedProcess)
        proc_mock.stdout = __DEFAULT_GIT_STDOUT
        proc_mock.stderr = __DEFAULT_GIT_STDERR
        proc_mock.returncode = __DEFAULT_GIT_EXIT_CODE
        return proc_mock

    return side_effect


def test_update_release_branch_fetch_errors(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "fetch", "origin", f"{release_config.release_branch}:{release_config.release_branch}"]
    next_command = ["git", "checkout", release_config.release_branch]
    subp_mock.side_effect = update_release_side_effect(fetch=False)
    result = commander.update_release_branch()

    assert not result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call(f"Error wile fetching origin/{release_config.release_branch}")
    assert call(f"Running command: '%s'", ' '.join(next_command)) not in log_debug_spy.mock_calls


def test_update_release_branch_checkout_errors(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "checkout", release_config.release_branch]
    next_command = ["git", "reset", "--hard", f"origin/{release_config.default_branch}"]
    subp_mock.side_effect = update_release_side_effect(checkout=False)
    result = commander.update_release_branch()

    assert not result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call("Error while checking out existing release branch")
    assert call(f"Running command: '%s'", ' '.join(next_command)) not in log_debug_spy.mock_calls


def test_update_release_branch_reset_errors(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "reset", "--hard", f"origin/{release_config.default_branch}"]
    subp_mock.side_effect = update_release_side_effect(reset=False)
    result = commander.update_release_branch()

    assert not result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call(f"Error while resetting branch to {release_config.default_branch}")
    assert call([f"Running command: '%s'", ' '.join(expected_command)]) not in log_debug_spy.mock_calls


def test_update_release_branch(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "reset", "--hard", f"origin/{release_config.default_branch}"]
    subp_mock.side_effect = update_release_side_effect()
    result = commander.update_release_branch()

    assert result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    assert call(f"Error while resetting branch to {release_config.default_branch}") not in log_error_spy.mock_calls
    assert call([f"Running command: '%s'", ' '.join(expected_command)]) not in log_debug_spy.mock_calls
