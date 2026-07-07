from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum

CONV_COMMIT_TYPES = ["feat", "fix", "refactor", "perf", "style", "test", "build", "ops", "docs", "chore", "merge"]
CONV_COMMIT_TYPE_PATTERN = f"^({"|".join(CONV_COMMIT_TYPES)})(\\([^)]*\\))?(!?):[ ]*(\\S.*)$"
CC_GROUP_TYPE = 1
CC_GROUP_SCOPE = 2
CC_GROUP_BREAKING_CHANGE = 3
CC_GROUP_DESCRIPTION = 4


@dataclass
class ResolvedCommitTitle:
    type_: str
    description: str
    scope: str | None
    breaking_change: bool


class ChangeType(IntEnum):
    NONE = 3
    PATCH = 2
    MINOR = 1
    MAJOR = 0


@dataclass
class GroupedConvCommits:
    valid_commits: dict[str, list[ConvCommitDetails]] = field(default_factory=dict)
    invalid_commits: list[ConvCommitDetails] = field(default_factory=list)
    braking_changes: list[ConvCommitDetails] = field(default_factory=list)

    def has_feature(self) -> bool:
        return "feat" in self.valid_commits.keys()

    def has_fix(self) -> bool:
        return "fix" in self.valid_commits.keys()

    def has_other_change(self) -> bool:
        keys = self.valid_commits.keys()
        return any((type_ not in ["feat", "fix"] and type_ in keys) for type_ in CONV_COMMIT_TYPES)

    def has_breaking_change(self) -> bool:
        return len(self.braking_changes) > 0

    def get_highest_change(self) -> ChangeType:
        if self.has_breaking_change():
            return ChangeType.MAJOR
        elif self.has_feature():
            return ChangeType.MINOR
        elif self.has_fix() or self.has_other_change():
            return ChangeType.PATCH
        else:
            return ChangeType.NONE

    def get_features(self) -> list[ConvCommitDetails]:
        return_value = []
        if self.has_feature():
            return_value = self.valid_commits["feat"]
        return return_value

    def get_fixes(self) -> list[ConvCommitDetails]:
        return_value = []
        if self.has_fix():
            return_value = self.valid_commits["fix"]
        return return_value

    def get_other_changes(self) -> list[ConvCommitDetails]:
        return_value = []
        keys = self.valid_commits.keys()
        for type_ in CONV_COMMIT_TYPES:
            if type_ in ["feat", "fix"]:
                continue
            if type_ in keys:
                return_value.extend(self.valid_commits[type_])
        return return_value


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
