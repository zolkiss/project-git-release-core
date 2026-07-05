from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from pgr.config.release_config import ReleaseConfig
from pgr.git import GitHashAndMsg
from pgr.semver_util import build_version_regex


class Connector(ABC):
    def __init__(self, config: ReleaseConfig):
        self.config = config

    @abstractmethod
    def get_latest_open_release_pr(self, state: str = "open") -> GitReleasePR | None: ...

    @abstractmethod
    def update_first_commit_pr(self, pull_request_id: str): ...

    @abstractmethod
    def get_latest_release(self) -> GitRelease | None: ...

    @abstractmethod
    def get_commit_details(self, commit_hash: GitHashAndMsg) -> CommitDetails | None: ...

    @abstractmethod
    def create_release_pr(self, pull_request_title: str, pull_request_commit_text: str) -> GitReleasePR | None: ...

    @abstractmethod
    def update_release_pr(self, release_pr_number: int, pull_request_title: str,
                          pull_request_commit_text: str) -> GitReleasePR | None: ...

    def validate_release_version(self, version: str) -> bool:
        return build_version_regex(self.config.release_version_prefix).match(version) is not None


@dataclass(frozen=True)
class GitReleasePR:
    id: int
    number: int
    title: str
    comment: str
    commit_sha: str


@dataclass(frozen=True)
class GitRelease:
    tag_name: str
    tag_message: str
    commit_sha: str


@dataclass(frozen=True)
class CommitDetails:
    hash: str
    title: str
    creation_time: datetime
    body: str | None
    footers: list[str]

    @classmethod
    def of(cls,
           hash_of: str, title_of: str,
           creation_time: datetime,
           body: str | None = None, footers: list[str] | None = None) -> CommitDetails:
        if footers is None:
            footers = []
        return cls(hash_of, title_of, creation_time, body, footers)


@dataclass(frozen=True)
class NewVersion:
    semver: str
    prefix: str

    def get_full_version(self):
        return f"{self.prefix}{self.semver}"

