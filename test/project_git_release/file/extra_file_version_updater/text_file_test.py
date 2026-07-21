from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable
from unittest.mock import MagicMock, mock_open

import pytest

from project_git_release.classes import NewVersion
from project_git_release.file import ExtraFileVersionUpdater

__TEST_TEMP_DIR = "test_temp_dir"


@pytest.fixture
def temp_dir():
    mock = MagicMock(spec=TemporaryDirectory)
    mock.name = __TEST_TEMP_DIR
    return mock


def file_side_effect(read_data: str = ''):
    m_read = mock_open(read_data=read_data)
    m_write = mock_open()

    def callback(file, *args, **kwargs):
        mode = args[0]
        if mode == 'r':
            return m_read(file, mode, *args, **kwargs)
        elif mode == 'w':
            return m_write(file, mode, *args, **kwargs)
        raise ValueError(f"Invalid mode: {mode}")

    return {'callback': callback, 'm_read': m_read, 'm_write': m_write}


def assert_valid_write_action(m_write: Callable[..., Any] | Any, message: str):
    m_write.return_value.write.assert_called_once()
    update_file_content = m_write.return_value.write.call_args[0][0]
    assert message == update_file_content


def test_update_files_no_extra_files(mocker, release_config, temp_dir):
    updater = ExtraFileVersionUpdater(release_config, extra_file_config={}, temp_dir=temp_dir)
    json_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_json_files")
    text_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_text_files")

    updater.update_files(NewVersion("0.1.0", prefix=""), False)
    json_spy.assert_not_called()
    text_spy.assert_not_called()


def test_update_files_extra_text_no_temp_dir_files(mocker, release_config, temp_dir):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)
    json_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_json_files")
    text_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_text_files")

    callback_obj = file_side_effect()
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)
    m_write.return_value.write.assert_not_called()
    m_read.return_value.readlines.assert_not_called()
    json_spy.assert_not_called()
    text_spy.assert_called_once()


def test_update_files_extra_text_without_marker(mocker, release_config, temp_dir, log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(read_data="custom_property_file=yes\nversion:0.1.0")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    m_write.return_value.write.assert_not_called()

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])
    log_info_spy.assert_any_call("Cannot find version maker in %s", text_file_config['text'][0])


def test_update_files_extra_text_with_line_marker(mocker, release_config, temp_dir, log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\nversion:0.0.1 #{release_config.version_config_marker}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\nversion:0.1.0 #{release_config.version_config_marker}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])


def test_update_files_extra_text_with_line_marker_but_no_valid_semver_version(mocker, release_config,
                                                                              temp_dir, log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\nversion:not-valid-semver #{release_config.version_config_marker}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\nversion:not-valid-semver #{release_config.version_config_marker}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])


def test_update_files_extra_text_with_line_marker_but_no_valid_semver_version_with_append(mocker, release_config,
                                                                                          temp_dir, log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\nversion:not-valid-semver #{release_config.version_config_marker}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), True)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\nversion:not-valid-semver 0.1.0 #{release_config.version_config_marker}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])


def test_update_files_extra_text_with_block_marker_no_change(mocker, release_config, temp_dir, log_info_spy,
                                                             log_warn_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:0.0.1\n#{release_config.version_config_marker_block_end}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.0.1", prefix=""), False)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:0.0.1\n#{release_config.version_config_marker_block_end}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])
    log_warn_spy.assert_any_call("No update happened in the marked lines")


def test_update_files_extra_text_with_block_marker(mocker, release_config, temp_dir, log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:0.0.1\n#{release_config.version_config_marker_block_end}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:0.1.0\n#{release_config.version_config_marker_block_end}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])


def test_update_files_extra_text_with_block_marker_missing_ending(mocker, release_config, temp_dir,
                                                                  log_info_spy, log_error_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\n#{release_config.version_config_marker_block_start}\nversion:0.0.1")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    m_write.return_value.write.assert_not_called()

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])
    log_error_spy.assert_any_call("Cannot find ending marker for starting marker at line %s", 2)


def test_update_files_extra_text_with_block_marker_with_no_semver(mocker, release_config, temp_dir, log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:\n#{release_config.version_config_marker_block_end}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:\n#{release_config.version_config_marker_block_end}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])


def test_update_files_extra_text_with_block_marker_with_no_semver_but_with_append(mocker, release_config, temp_dir,
                                                                                  log_info_spy):
    text_file_config = {'text': ['very_file.txt']}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=text_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    callback_obj = file_side_effect(
        read_data=f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion:\n#{release_config.version_config_marker_block_end}")
    m_write = callback_obj["m_write"]
    m_read = callback_obj["m_read"]
    mocker.patch("builtins.open", side_effect=callback_obj["callback"])

    updater.update_files(NewVersion("0.1.0", prefix=""), True)

    assert_valid_write_action(m_write,
                              f"custom_property_file=yes\n{release_config.version_config_marker_block_start}\nversion: 0.1.0\n#{release_config.version_config_marker_block_end}")

    m_read.return_value.readlines.assert_called_once()

    log_info_spy.assert_any_call("Updating version in %s", text_file_config['text'][0])
