from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import MagicMock, mock_open

import pytest

from project_git_release.classes import NewVersion
from project_git_release.classes.conv_commit import GroupedConvCommits, ConvCommitDetails
from project_git_release.common.changelog_generator import ChangelogGenerator

_DEFAULT_TEMP_DIR = "//temp_dir"


class FileSideEffect:
    def __init__(self, callback: Any, read: MagicMock, write: MagicMock):
        self.cb = callback
        self.read = read
        self.write = write


@pytest.fixture
def temp_dir():
    temp_dir = MagicMock(spec=TemporaryDirectory)
    temp_dir.name = _DEFAULT_TEMP_DIR
    return temp_dir


@pytest.fixture
def change_gen(release_config, temp_dir):
    return ChangelogGenerator(release_config, temp_dir)


def cl_file_sideeffect(read_data: str = "") -> FileSideEffect:
    # Use like this: mocker.patch("builtins.open", side_effect=file_side_effect(read_data=json.dumps({'version': '0.0.1'})))
    m_read = mock_open(read_data=read_data)
    m_write = mock_open()

    def callback(file, *args, **kwargs):
        mode = args[0]
        if mode == 'r':
            return m_read(file, mode, *args, **kwargs)
        elif mode == 'w+':
            return m_write(file, mode, *args, **kwargs)
        raise ValueError(f"Invalid mode: {mode}")

    return FileSideEffect(callback, m_read, m_write)


def test_create_new_changelog(mocker, change_gen, release_config, log_info_spy):
    valid_commit_desc = "Valid commit"
    invalid_commit_desc = "Invalid commit"
    bugfix_01_desc = "BugFix_01"
    bugfix_01_scope = "BF_01"
    bugfix_02_desc = "BugFix_02"
    other_desc = "Very other task"
    other_scope = "OTH_01"
    breaking_change_desc = "BREAK EVERYTHING"

    commits = GroupedConvCommits(valid_commits=
    {"feat": [
        ConvCommitDetails.valid_commit("feat", datetime.now(), valid_commit_desc)
    ], "fix": [
        ConvCommitDetails.valid_commit("fix", datetime.now(), bugfix_01_desc, scope=bugfix_01_scope),
        ConvCommitDetails.valid_commit("fix", datetime.now(), bugfix_02_desc)
    ], "test": [
        ConvCommitDetails.valid_commit("test", datetime.now(), other_desc, scope=other_scope)
    ]}, invalid_commits=[
        ConvCommitDetails.invalid_commit(datetime.now(), invalid_commit_desc)
    ], braking_changes=[
        ConvCommitDetails.valid_commit("feat", datetime.now(), breaking_change_desc)
    ])

    cl_file = cl_file_sideeffect()
    mocker.patch("builtins.open", side_effect=cl_file.cb)

    new_version = "0.1.0"
    change_gen.generate_changelog(commits, None, NewVersion(new_version, ""))

    log_info_spy.assert_any_call("No %s file is present. Creating one...", "CHANGELOG.md")
    cl_file.write.assert_any_call(f"{_DEFAULT_TEMP_DIR}/{release_config.changelog_file}", "w+", "w+", encoding='UTF-8')
    written_content = cl_file.write.return_value.write.call_args[0][0]

    today = datetime.now()

    assert -1 != written_content.find(today.strftime("%Y-%m-%d"))
    assert -1 != written_content.find("## Changelog")
    assert -1 != written_content.find(f"## [{new_version}]({release_config.git_url()}/releases/tag/{new_version})")
    assert -1 != written_content.find(f"### Features\n*  {valid_commit_desc}")
    assert -1 != written_content.find(f"### Bugfix(es)\n*  {bugfix_02_desc}\n* **{bugfix_01_scope}:** {bugfix_01_desc}")
    assert -1 != written_content.find(
        f"### Other changes\n* {invalid_commit_desc}\n* **test({other_scope}):** {other_desc}")
    assert -1 != written_content.find(f"### Breaking changes\n*  {breaking_change_desc}")


def test_update_existing_version(mocker, change_gen, release_config, log_info_spy):
    valid_commit_desc = "Valid commit"
    commits = GroupedConvCommits(valid_commits=
    {"feat": [
        ConvCommitDetails.valid_commit("feat", datetime.now(), valid_commit_desc)
    ]})

    cl_file = cl_file_sideeffect("## Changelog\n### Features\n*  PreviousStuff")
    mocker.patch("builtins.open", side_effect=cl_file.cb)
    mocker.patch.object(Path, "exists", return_value=True)

    new_version = "0.1.0"
    change_gen.generate_changelog(commits, "0.0.1", NewVersion(new_version, ""))

    cl_file.write.assert_any_call(f"{_DEFAULT_TEMP_DIR}/{release_config.changelog_file}", "w+", "w+", encoding='UTF-8')
    written_content = cl_file.write.return_value.write.call_args[0][0]

    today = datetime.now()
    assert -1 != written_content.find(today.strftime("%Y-%m-%d"))
    assert -1 != written_content.find("## Changelog")
    assert -1 != written_content.find(f"## [{new_version}]({release_config.git_url()}/releases/tag/{new_version})")
    assert -1 != written_content.find(f"### Features\n*  {valid_commit_desc}")
    assert -1 != written_content.find(f"### Features\n*  PreviousStuff")
