import json
from pathlib import Path
from tempfile import TemporaryDirectory
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


@pytest.fixture
def json_load(mocker):
    return mocker.spy(json, "load")


@pytest.fixture
def json_dump(mocker):
    return mocker.spy(json, "dump")


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

    return callback


def compare_dictionaries(dump_param: dict, expected_result: dict) -> bool:
    expected_keys = expected_result.keys()
    dump_keys = dump_param.keys()

    if expected_keys != dump_keys:
        return False

    return_value = True
    for key in expected_keys:
        dump_value = dump_param[key]
        expected_value = expected_result[key]

        if type(dump_value) == dict and type(expected_value) == dict:
            return_value = return_value and compare_dictionaries(dump_value, expected_value)
        else:
            return_value = return_value and (dump_value == expected_value)

        if not return_value:
            return return_value

    return return_value


# def assert_valid_write_action(json_write, message: str):
#     m_write.return_value.write.assert_called_once()
#     update_file_content = m_write.return_value.write.call_args[0][0]
#     assert message == update_file_content


def test_update_files_extra_json_no_temp_dir_files(mocker, release_config, temp_dir, json_load, json_dump):
    json_file_config = {'json': [{'repo_path': 'very_file.json', 'version_path': '.version'}]}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=json_file_config, temp_dir=temp_dir)
    json_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_json_files")
    text_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_text_files")

    mocker.patch("builtins.open", side_effect=file_side_effect(read_data=json.dumps({'version': '0.0.1'})))

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    json_spy.assert_called_once()
    text_spy.assert_not_called()

    json_load.assert_not_called()
    json_dump.assert_not_called()


def test_update_files_extra_json_invalid_config(mocker, release_config, temp_dir, json_load, json_dump, log_error_spy):
    json_file_config = {'json': [{'repo_path': 'very_file.json'}]}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=json_file_config, temp_dir=temp_dir)
    json_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_json_files")
    text_spy: MagicMock = mocker.spy(updater, "_ExtraFileVersionUpdater__update_text_files")

    mocker.patch("builtins.open", side_effect=file_side_effect(read_data=json.dumps({'version': '0.0.1'})))

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    json_spy.assert_called_once()
    text_spy.assert_not_called()

    json_load.assert_not_called()
    json_dump.assert_not_called()

    log_error_spy.assert_any_call(
        "Invalid configuration. In case of JSON Extra file the non empty repo_path and version_path keys are needed")


def test_update_files_extra_json_invalid_path(mocker, release_config, temp_dir, log_warn_spy, json_load, json_dump):
    json_file_config = {'json': [{'repo_path': 'very_file.json', 'version_path': '$.not.valid.path'}]}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=json_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    mocker.patch("builtins.open", side_effect=file_side_effect(read_data=json.dumps({'version': '0.0.1'})))

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    json_dump.assert_not_called()
    json_load.assert_called_once()
    log_warn_spy.assert_any_call("Cannot find version path (%s) in the %s file", '$.not.valid.path', 'very_file.json')


def test_update_files_extra_json_invalid_path_with_add(mocker, release_config, temp_dir, log_warn_spy, json_load,
                                                       json_dump):
    json_file_config = {
        'json': [{'repo_path': 'very_file.json', 'version_path': '$.not.valid.path', 'create_property': True}]}
    updater = ExtraFileVersionUpdater(release_config, extra_file_config=json_file_config, temp_dir=temp_dir)

    path_exists_mock = mocker.patch.object(Path, "exists")
    path_exists_mock.return_value = True

    mocker.patch("builtins.open", side_effect=file_side_effect(read_data=json.dumps({'version': '0.0.1'})))

    updater.update_files(NewVersion("0.1.0", prefix=""), False)

    json_dump.assert_called_once()
    dict_written: dict = json_dump.call_args[0][0]
    expected_result = {'not': {'valid': {'path': '0.1.0'}}, 'version': '0.0.1'}
    assert compare_dictionaries(dict_written, expected_result)
    json_load.assert_called_once()
