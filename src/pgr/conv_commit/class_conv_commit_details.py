from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConvCommitDetails:
    valid: bool
    description: str
    breaking_change: bool
    creation_datetime: datetime
    type: str | None
    body: str | None
    scope: str | None
    footer: list[str] | None

    @classmethod
    def invalid_commit(cls, creation_datetime: datetime, description: str) -> ConvCommitDetails:
        return ConvCommitDetails(False, description, False, creation_datetime, None, None, None, [])

    @classmethod
    def valid_commit(cls, type_: str, creation_datetime: datetime, description: str, breaking_change: bool = False,
                     body: str | None = None,
                     scope: str | None = None, footers: list[str] | None = None) -> ConvCommitDetails:
        if footers is None:
            footers = []
        return ConvCommitDetails(True, description, breaking_change, creation_datetime, type_, body, scope, footers)
