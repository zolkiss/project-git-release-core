from importlib.metadata import EntryPoint
from pathlib import Path
from unittest.mock import mock_open, MagicMock

import pytest
from typer.testing import CliRunner

from project_git_release import Connector, ReleaseEngine
from project_git_release.runner import app

runner = CliRunner()

_DUMMY_ENTRY_POINT_NAME = "dummy-ep"
_DUMMY_CONNECTOR_NAME = "dummy-connector"


def no_connector_mock_setup(mocker):
    mocker.patch("project_git_release.runner.entry_points", return_value=[])


@pytest.fixture
def dummy_connector(mocker):
    connector = MagicMock(spec=Connector)
    connector.name = _DUMMY_ENTRY_POINT_NAME

    entry_point = MagicMock(spec=EntryPoint)
    entry_point.name = _DUMMY_ENTRY_POINT_NAME
    entry_point.load.return_value = connector

    mocker.patch("project_git_release.runner.entry_points", return_value=[entry_point])
    return connector


def test_runner_listing_envs():
    result = runner.invoke(app, ["--list-env"])

    assert result.exit_code == 0
    assert result.stdout.find("Available PGR_* environment variables:") != -1


def test_runner_not_existing_env_path_file(release_config, log_error_spy):
    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--env-file-path=not_valid.txt"],
                           catch_exceptions=False)

    assert result.exit_code == 1
    log_error_spy.assert_any_call("Cannot find environment file on path %s", "not_valid.txt")


def test_runner_parameters_missing_params():
    result = runner.invoke(app, [])

    assert result.exit_code == 2
    assert result.stderr.find("Invalid value: Invalid repo configuration. The git-repo-url, git-repo-owner") != -1
    assert result.stderr.find("and git-repo-name needs to be set via options or env variables") != -1


def test_runner_parameters_no_token_value(release_config):
    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}"],
                           catch_exceptions=False)

    assert result.exit_code == 2
    assert result.stderr.find("Invalid value for --git-token-env-var: Cannot find PGR_TOKEN in the") != -1


def test_runner_parameters_both_token_values_used(release_config):
    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-env-var=ENV_VAR",
                                 "--git-token-file=token.txt"],
                           catch_exceptions=False)

    assert result.exit_code == 2
    assert result.stderr.find("Invalid value: Invalid configuration. --git-token-env-var and") != -1
    assert result.stderr.find("--git-token-file cannot be used in the same time") != -1


def test_runner_parameters_file_token_not_exists(release_config):
    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt"],
                           catch_exceptions=False)

    assert result.exit_code == 2
    assert result.stderr.find("Cannot find token.txt, or it is not") != -1


def test_runner_parameters_file_token_exists_but_empty(release_config, mocker):
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch.object(Path, "is_file", return_value=True)
    m_read = mock_open(read_data="")
    mocker.patch("builtins.open", side_effect=m_read)

    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt"],
                           catch_exceptions=False)

    assert result.exit_code == 2
    assert result.stderr.find("Invalid value for --git-token-file: The token file token.txt is empty") != -1


def test_runner_parameters_file_token_exists_and_valid(release_config, mocker, log_error_spy):
    create_valid_token_setup(mocker)

    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt"],
                           catch_exceptions=False)

    assert result.exit_code == 1
    log_error_spy.assert_any_call("Unsupported operation so far...")


def test_no_connector_setup(release_config, mocker):
    create_valid_token_setup(mocker)
    no_connector_mock_setup(mocker)

    with pytest.raises(ValueError) as value_error:
        runner.invoke(app, [f"--git-repo-url={release_config.url}",
                            f"--git-repo-owner={release_config.owner}",
                            f"--git-repo-name={release_config.repo}",
                            "--git-token-file=token.txt"],
                      catch_exceptions=False)


def test_connector_cannot_found_by_name(release_config, mocker, dummy_connector):
    create_valid_token_setup(mocker)

    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt",
                                 "--connector=not-valid"],
                           catch_exceptions=False)

    assert result.exit_code == 2
    assert result.stderr.find("Invalid connector is set: not-valid") != -1


def test_connector_found_by_name(release_config, mocker, dummy_connector, log_error_spy):
    create_valid_token_setup(mocker)
    release_engine = MagicMock(spec=ReleaseEngine)
    mocker.patch.object(ReleaseEngine, "__new__", return_value=release_engine)
    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt",
                                 f"--connector={_DUMMY_ENTRY_POINT_NAME}"],
                           catch_exceptions=False)

    assert 1 == result.exit_code
    log_error_spy.assert_any_call("Unsupported operation so far...")


def test_update_called(release_config, mocker, dummy_connector):
    create_valid_token_setup(mocker)
    release_engine = MagicMock(spec=ReleaseEngine)
    mocker.patch.object(ReleaseEngine, "__new__", return_value=release_engine)

    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt", "update"],
                           catch_exceptions=False)

    assert 0 == result.exit_code
    release_engine.update_version.assert_called_once()
    release_engine.release_unreleased_prs.assert_not_called()


def test_release_called(release_config, mocker, dummy_connector):
    create_valid_token_setup(mocker)
    release_engine = MagicMock(spec=ReleaseEngine)
    mocker.patch.object(ReleaseEngine, "__new__", return_value=release_engine)

    result = runner.invoke(app, [f"--git-repo-url={release_config.url}", f"--git-repo-owner={release_config.owner}",
                                 f"--git-repo-name={release_config.repo}", "--git-token-file=token.txt", "release"],
                           catch_exceptions=False)

    assert 0 == result.exit_code
    release_engine.release_unreleased_prs.assert_called_once()
    release_engine.update_version.assert_not_called()


def create_valid_token_setup(mocker):
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch.object(Path, "is_file", return_value=True)
    m_read = mock_open(read_data="EPIC_TOKEN_VALUE")
    mocker.patch("builtins.open", side_effect=m_read)
