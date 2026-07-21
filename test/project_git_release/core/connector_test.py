import pytest

from project_git_release.test_classes import DummyConnector


@pytest.fixture
def connector(release_config):
    return DummyConnector(release_config)


def test_validate_versions(release_config, connector):
    assert connector.validate_release_version("1.0.0")
    assert not connector.validate_release_version("random_version")

    release_config.release_version_prefix = "custom-service-"
    assert connector.validate_release_version("custom-service-0.0.1")
    assert connector.validate_release_version("custom-service-0.0.1-past001")
    assert not connector.validate_release_version("customer-service-0.0.1-past001")
