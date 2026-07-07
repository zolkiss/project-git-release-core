from abc import abstractmethod, ABC

from pgr.classes.data_classes import GitRelease, GitReleaseResponse, GitReleasePR, GitHashAndMsg, CommitDetails
from pgr.config import ReleaseConfig
from pgr.semver_util import build_version_regex


class Connector(ABC):
    def __init__(self, config: ReleaseConfig):
        self.config = config

    @abstractmethod
    def get_latest_release_pr(self, state: str) -> GitReleasePR | None: ...

    @abstractmethod
    def get_latest_release_prs(self, state: str, limit=10) -> list[GitReleasePR]: ...

    @abstractmethod
    def get_latest_release(self) -> GitRelease | None: ...

    @abstractmethod
    def get_release_by_tag(self, tag: str) -> GitRelease | None: ...

    @abstractmethod
    def get_commit_details(self, commit_hash: GitHashAndMsg) -> CommitDetails | None: ...

    @abstractmethod
    def create_release_pr(self, pull_request_title: str, pull_request_commit_text: str) -> GitReleasePR | None: ...

    @abstractmethod
    def update_release_pr(self, release_pr_number: int, pull_request_title: str,
                          pull_request_commit_text: str) -> GitReleasePR | None: ...

    @abstractmethod
    def create_release(self, latest_unreleased_version: GitRelease, change_log: str, draft: bool = False,
                       pre_release: bool = False) -> GitReleaseResponse: ...

    def validate_release_version(self, version: str) -> bool:
        return build_version_regex(self.config.release_version_prefix).match(version) is not None
