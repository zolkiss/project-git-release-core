from dataclasses import dataclass


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
