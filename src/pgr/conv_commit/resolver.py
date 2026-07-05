import re
from dataclasses import dataclass, field
from enum import IntEnum

from pgr.conv_commit.class_conv_commit_details import ConvCommitDetails
from pgr.interfaces import CommitDetails

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


def __resolve_commit_title(title: str) -> ResolvedCommitTitle | None:
    match = re.match(CONV_COMMIT_TYPE_PATTERN, title)
    if match is None:
        return None

    type_ = match.group(CC_GROUP_TYPE)
    scope = match.group(CC_GROUP_SCOPE)
    if scope in ['', '()', None]:
        scope = None
    else:
        scope = scope.lstrip("(").rstrip(")")
    description = match.group(CC_GROUP_DESCRIPTION)
    breaking_change = match.group(CC_GROUP_BREAKING_CHANGE) == "!"

    return ResolvedCommitTitle(type_, description, scope, breaking_change)


def resolve_commit_message(commit: CommitDetails) -> ConvCommitDetails | None:
    commit_title = __resolve_commit_title(commit.title)

    if commit_title is None:
        return ConvCommitDetails.invalid_commit(commit.creation_time, commit.title)

    footer_breaking_change = any(footer.startswith("BREAKING CHANGE:") for footer in commit.footers)

    return ConvCommitDetails.valid_commit(commit_title.type_, commit.creation_time, commit_title.description,
                                          breaking_change=(commit_title.breaking_change or footer_breaking_change),
                                          scope=commit_title.scope, body=commit.body, footers=commit.footers)


def resolve_commit_messages(commit_list: list[CommitDetails]) -> list[ConvCommitDetails]:
    return [
        conv_commit
        for commit in commit_list if (conv_commit := resolve_commit_message(commit)) is not None
    ]


def group_conv_commit_details(conv_commits: list[ConvCommitDetails]) -> GroupedConvCommits:
    grouped_values = GroupedConvCommits()
    for conv_commit in conv_commits:
        if not conv_commit.valid or conv_commit.type is None:
            grouped_values.invalid_commits.append(conv_commit)
            continue

        type_ = conv_commit.type

        if conv_commit.breaking_change:
            grouped_values.braking_changes.append(conv_commit)
        elif type_ not in grouped_values.valid_commits.keys():
            grouped_values.valid_commits[type_] = [conv_commit]
        else:
            grouped_values.valid_commits[type_].append(conv_commit)
    return grouped_values
