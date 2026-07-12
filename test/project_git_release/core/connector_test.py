import pytest

from project_git_release import Connector
from project_git_release.classes import GitRelease, GitReleaseResponse, GitReleasePR, GitHashAndMsg, CommitDetails


@pytest.fixture
def test_connector(release_config):
    class TestConnector(Connector):
        def get_latest_release_pr(self, state: str) -> GitReleasePR | None:
            pass

        def get_latest_release_prs(self, state: str, limit=10) -> list[GitReleasePR]:
            pass

        def get_latest_release(self) -> GitRelease | None:
            pass

        def get_release_by_tag(self, tag: str) -> GitRelease | None:
            pass

        def get_commit_details(self, commit_hash: GitHashAndMsg) -> CommitDetails | None:
            pass

        def create_release_pr(self, pull_request_title: str, pull_request_commit_text: str) -> GitReleasePR | None:
            pass

        def update_release_pr(self, release_pr_number: int, pull_request_title: str,
                              pull_request_commit_text: str) -> GitReleasePR | None:
            pass

        def create_release(self, latest_unreleased_version: GitRelease, change_log: str, draft: bool = False,
                           pre_release: bool = False) -> GitReleaseResponse:
            pass

    return TestConnector(release_config)


def test_validate_versions(release_config, test_connector):
    assert test_connector.validate_release_version("1.0.0")
    assert not test_connector.validate_release_version("random_version")

    release_config.release_version_prefix = "custom-service-"
    assert test_connector.validate_release_version("custom-service-0.0.1")
    assert test_connector.validate_release_version("custom-service-0.0.1-past001")
    assert not test_connector.validate_release_version("customer-service-0.0.1-past001")
