import re

from project_git_release.classes import CommitDetails
from project_git_release.classes.conv_commit import ResolvedCommitTitle, CONV_COMMIT_TYPE_PATTERN, CC_GROUP_TYPE, \
    CC_GROUP_SCOPE, \
    CC_GROUP_DESCRIPTION, CC_GROUP_BREAKING_CHANGE, ConvCommitDetails, GroupedConvCommits, CONV_COMMIT_TYPES


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


def __resolve_commit_message(commit: CommitDetails) -> ConvCommitDetails | None:
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
        for commit in commit_list if (conv_commit := __resolve_commit_message(commit)) is not None
    ]


def group_conv_commit_details(conv_commits: list[ConvCommitDetails]) -> GroupedConvCommits:
    grouped_values = GroupedConvCommits()
    for conv_commit in conv_commits:
        if (not conv_commit.valid
                or conv_commit.type is None
                or conv_commit.type not in CONV_COMMIT_TYPES):
            grouped_values.invalid_commits.append(conv_commit)
            continue

        type_ = conv_commit.type

        if conv_commit.breaking_change:
            grouped_values.breaking_changes.append(conv_commit)
        elif type_ not in grouped_values.valid_commits.keys():
            grouped_values.valid_commits[type_] = [conv_commit]
        else:
            grouped_values.valid_commits[type_].append(conv_commit)
    return grouped_values
