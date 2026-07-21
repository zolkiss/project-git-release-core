from importlib.metadata import EntryPoint
from unittest.mock import MagicMock

import pytest

from project_git_release.registry import get_connector

__VALID_ENTRY_POINT_NAME = "valid_entry_point"
__INVALID_ENTRY_POINT_NAME = "invalid_entry_point"


@pytest.fixture
def valid_ep():
    ep = MagicMock(spec=EntryPoint)
    ep.name = __VALID_ENTRY_POINT_NAME
    return ep


@pytest.fixture
def entry_points(mocker, valid_ep):
    return mocker.patch("project_git_release.registry.entry_points", return_value=[valid_ep])


def test_get_connector_no_connector(entry_points):
    with pytest.raises(ValueError):
        get_connector(__INVALID_ENTRY_POINT_NAME)


def test_get_connector(entry_points, valid_ep):
    connector = get_connector(__VALID_ENTRY_POINT_NAME)

    assert connector is not None
    valid_ep.load.assert_called_once()
