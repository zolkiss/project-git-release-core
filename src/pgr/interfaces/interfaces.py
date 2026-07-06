from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GitReleasePR:
    id: int
    number: int
    title: str
    comment: str
    commit_sha: str
    merged: bool


@dataclass(frozen=True)
class GitRelease:
    tag_name: str
    tag_message: str
    commit_sha: str


@dataclass(frozen=True)
class GitReleaseResponse:
    tag_name: str
    name: str
    commit_sha: str
    id: int
    draft: bool
    pre_release: bool


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


@dataclass(frozen=True)
class GitCmdResult:
    result: bool
    stdout: str
    stderr: str
    return_code: int


@dataclass(frozen=True)
class GitHashAndMsg:
    hash: str
    message: str
