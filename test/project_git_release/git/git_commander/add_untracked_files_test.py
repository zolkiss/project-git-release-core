import subprocess
from unittest.mock import MagicMock, call

from conftest import __DEFAULT_GIT_STDOUT, __DEFAULT_GIT_STDERR, __DEFAULT_GIT_EXIT_CODE


def add_untracked_files_side_effect(first_ls: bool = True,
                                    second_ls: bool = True,
                                    first_lines: list[str] | None = None,
                                    second_lines: list[str] | None = None):
    occurrences = {}

    def side_effect(*args, **kwargs):
        key = args[0][1]
        occurrences[key] = occurrences.get(key, 0) + 1
        occurrence = occurrences[key]

        proc_mock = MagicMock(spec=subprocess.CompletedProcess)
        proc_mock.stdout = __DEFAULT_GIT_STDOUT
        proc_mock.stderr = __DEFAULT_GIT_STDERR
        proc_mock.returncode = __DEFAULT_GIT_EXIT_CODE

        if key == "ls-files" and occurrence == 1:
            if not first_ls:
                raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")
            else:
                proc_mock.stdout = '\n'.join(first_lines or [])
        if key == "ls-files" and occurrence == 2:
            if not second_ls:
                raise subprocess.CalledProcessError(1, ' '.join(args[0]), "", "")
            else:
                proc_mock.stdout = '\n'.join(second_lines or [])
        return proc_mock

    return side_effect


def test_add_untracked_first_files_errors(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "ls-files", "-o", "-m", "-d"]
    subp_mock.side_effect = add_untracked_files_side_effect(first_ls=False)

    result = commander.add_untracked_files()
    assert not result

    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    log_error_spy.assert_any_call("Error while listing untracked files")


def test_add_untracked_file_remaining_files(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "ls-files", "-o", "-m", "-d"]
    subp_mock.side_effect = add_untracked_files_side_effect(first_lines=["test_01.txt", "test_02.txt"],
                                                            second_lines=["test_02.txt"])

    result = commander.add_untracked_files()
    assert not result

    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    assert call("Error while listing untracked files") not in log_error_spy.mock_calls


def test_add_untracked_file(subp_mock, commander, release_config, log_error_spy, log_debug_spy):
    expected_command = ["git", "ls-files", "-o", "-m", "-d"]
    first_lines = ["test_01.txt", "test_02.txt"]
    subp_mock.side_effect = add_untracked_files_side_effect(first_lines=first_lines)

    result = commander.add_untracked_files()
    assert result
    log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(expected_command))
    for line in first_lines:
        log_debug_spy.assert_any_call(f"Running command: '%s'", ' '.join(["git", "add", line]))
    assert call("Error while listing untracked files") not in log_error_spy.mock_calls
