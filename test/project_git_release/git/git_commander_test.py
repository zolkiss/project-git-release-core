import subprocess

from conftest import __TEST_TEMP_DIR


def test_clone_repository(subp_mock, commander, release_config):
    clone_result = commander.clone_repository()
    assert clone_result

    assert ['git', 'clone', release_config.git_url(), __TEST_TEMP_DIR, '--no-verbose'] == subp_mock.call_args.args[0]


def test_clone_repository_cmd_line_error(subp_mock, commander, release_config, log_error_spy):
    expected_command = ['git', 'clone', release_config.git_url(), __TEST_TEMP_DIR, '--no-verbose']
    expected_err_output = "ERROR_STD"
    expected_err_error = "ERROR_ERR"
    subp_mock.side_effect = subprocess.CalledProcessError(1, ' '.join(expected_command), expected_err_output,
                                                          expected_err_error)

    clone_result = commander.clone_repository()
    assert not clone_result
    assert expected_command == subp_mock.call_args.args[0]

    log_error_spy.assert_any_call(f"Error while cloning repository: {release_config.git_url()}")
    log_error_spy.assert_any_call(f"\n{expected_err_error}")


def test_is_release_branch_exists(subp_mock, commander, release_config, log_info_spy):
    clone_result = commander.is_release_branch_exists()
    assert clone_result

    assert ["git", "ls-remote", "--exit-code", "origin", release_config.release_branch] == subp_mock.call_args.args[0]


def test_create_release_branch(subp_mock, commander, release_config, log_info_spy):
    clone_result = commander.create_release_branch()
    assert clone_result

    assert ["git", "checkout", "-b", release_config.release_branch] == subp_mock.call_args.args[0]
