from project_git_release import Connector
from project_git_release.classes import GitReleasePR, GitRelease, GitHashAndMsg, CommitDetails, GitReleaseResponse
from project_git_release.core import ReleaseConfig


class DummyConnector(Connector):
    def __init__(self, config: ReleaseConfig):
        super().__init__(config)

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
