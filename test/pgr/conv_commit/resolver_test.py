from datetime import datetime

import pytest

from pgr.conv_commit import ConvCommitDetails, resolver
from pgr.conv_commit.resolver import ChangeType
from pgr.interfaces import CommitDetails


@pytest.mark.parametrize(
    argnames="commit_details, expected",
    argvalues=[
        pytest.param(CommitDetails.of("", "feat: Valid commit no scope without breaking change",
                                      datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0),
                                                    "Valid commit no scope without breaking change"),
                     id="Valid - no scope - not breaking"),
        pytest.param(
            CommitDetails.of("", "feat!: Valid commit no scope with breaking change", datetime(2025, 10, 10, 0, 0, 0)),
            ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0),
                                           "Valid commit no scope with breaking change",
                                                    breaking_change=True),
                     id="Valid - no scope - breaking"),
        pytest.param(
            CommitDetails.of("", "feat(): Valid commit with empty scope and without breaking change",
                             datetime(2025, 10, 10, 0, 0, 0)),
            ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0),
                                           "Valid commit with empty scope and without breaking change"),
            id="Valid - empty scope - not breaking"),
        pytest.param(CommitDetails.of("", "feat()!: Valid commit with empty scope and breaking change",
                                      datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0),
                                                    "Valid commit with empty scope and breaking change",
                                                    breaking_change=True),
                     id="Valid - empty scope - breaking"),
        pytest.param(CommitDetails.of("", "feat(valid_scope): Valid commit with scope and without breaking change",
                                      datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0),
                                                    "Valid commit with scope and without breaking change",
                                                    scope="valid_scope"),
                     id="Valid - with scope - not breaking"),
        pytest.param(
            CommitDetails.of("", "feat(valid_scope)!: Valid commit with scope and breaking change",
                             datetime(2025, 10, 10, 0, 0, 0)),
            ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0),
                                           "Valid commit with scope and breaking change",
                                           breaking_change=True,
                                           scope="valid_scope"),
            id="Valid - with scope - breaking"),
        pytest.param(CommitDetails.of("", "fix: Valid fix", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Valid fix"),
                     id="Valid - fix"),
        pytest.param(CommitDetails.of("", "refactor: Valid refactor", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("refactor", datetime(2025, 10, 10, 0, 0, 0), "Valid refactor"),
                     id="Valid - refactor"),
        pytest.param(CommitDetails.of("", "perf: Valid perf", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("perf", datetime(2025, 10, 10, 0, 0, 0), "Valid perf"),
                     id="Valid - perf"),
        pytest.param(CommitDetails.of("", "style: Valid style", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("style", datetime(2025, 10, 10, 0, 0, 0), "Valid style"),
                     id="Valid - style"),
        pytest.param(CommitDetails.of("", "test: Valid test", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("test", datetime(2025, 10, 10, 0, 0, 0), "Valid test"),
                     id="Valid - test"),
        pytest.param(CommitDetails.of("", "build: Valid build", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("build", datetime(2025, 10, 10, 0, 0, 0), "Valid build"),
                     id="Valid - build"),
        pytest.param(CommitDetails.of("", "ops: Valid ops", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("ops", datetime(2025, 10, 10, 0, 0, 0), "Valid ops"),
                     id="Valid - ops"),
        pytest.param(CommitDetails.of("", "docs: Valid docs", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("docs", datetime(2025, 10, 10, 0, 0, 0), "Valid docs"),
                     id="Valid - docs"),
        pytest.param(CommitDetails.of("", "chore: Valid chore", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("chore", datetime(2025, 10, 10, 0, 0, 0), "Valid chore"),
                     id="Valid - chore"),
        pytest.param(CommitDetails.of("", "merge: Valid merge", datetime(2025, 10, 10, 0, 0, 0)),
                     ConvCommitDetails.valid_commit("merge", datetime(2025, 10, 10, 0, 0, 0), "Valid merge"),
                     id="Valid - merge"),
    ]
)
def test_valid_cases_without_body(commit_details: CommitDetails, expected: str | None):
    conv_commit_details = resolver.resolve_commit_message(commit_details)
    assert conv_commit_details == expected


def test_body_value_copied():
    conv_commit_details = resolver.resolve_commit_message(
        CommitDetails("", "feat: valid", datetime(2025, 10, 10, 0, 0, 0), "body_value", []))
    assert conv_commit_details == ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "valid",
                                                                 body="body_value")


def test_footers_copied():
    conv_commit_details = resolver.resolve_commit_message(
        CommitDetails("", "feat: valid", datetime(2025, 10, 10, 0, 0, 0), None, ["Footer01", "Footer02"]))
    assert conv_commit_details == ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "valid",
                                                                 footers=["Footer01", "Footer02"])


def test_footer_overrides_breaking_change():
    conv_commit_details = resolver.resolve_commit_message(
        CommitDetails("", "feat: valid", datetime(2025, 10, 10, 0, 0, 0), None,
                      ["BREAKING CHANGE: Footer01", "Footer02"]))
    assert conv_commit_details == ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "valid",
                                                                 breaking_change=True,
                                                                 footers=["BREAKING CHANGE: Footer01", "Footer02"])


def test_2nd_footer_overrides_breaking_change():
    conv_commit_details = resolver.resolve_commit_message(
        CommitDetails("", "feat: valid", datetime(2025, 10, 10, 0, 0, 0), None,
                      ["Footer01", "BREAKING CHANGE: Footer02"]))
    assert conv_commit_details == ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "valid",
                                                                 breaking_change=True,
                                                                 footers=["Footer01", "BREAKING CHANGE: Footer02"])


@pytest.mark.parametrize(
    argnames="commit_title",
    argvalues=[
        pytest.param("feat[valid_scope]: Valid description", id="Wrong scope parenthesis"),
        pytest.param("faet: Valid description", id="Typo"),
        pytest.param("feat Valid description", id="Missing \":\""),
        pytest.param("feat:", id="No description"),
    ])
def test_invalid_cases(commit_title: str):
    conv_commit_details = resolver.resolve_commit_message(
        CommitDetails("", commit_title, datetime(2025, 10, 10, 0, 0, 0), None, []))
    assert conv_commit_details == ConvCommitDetails.invalid_commit(datetime(2025, 10, 10, 0, 0, 0), commit_title)


def test_grouping_features_only_no_breaking_change():
    grouped_conv_commits = resolver.group_conv_commit_details([
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 01"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 02"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 03"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 04"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 05")
    ])

    assert not grouped_conv_commits.has_breaking_change()
    assert not grouped_conv_commits.has_other_change()
    assert grouped_conv_commits.has_feature()
    assert not grouped_conv_commits.has_fix()
    assert grouped_conv_commits.get_highest_change() == ChangeType.MINOR


def test_grouping_fixes_only_no_breaking_change():
    grouped_conv_commits = resolver.group_conv_commit_details([
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 01"),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 02"),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 03"),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 04"),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 05")
    ])

    assert not grouped_conv_commits.has_breaking_change()
    assert not grouped_conv_commits.has_other_change()
    assert not grouped_conv_commits.has_feature()
    assert grouped_conv_commits.has_fix()
    assert grouped_conv_commits.get_highest_change() == ChangeType.PATCH


def test_grouping_mixed_other_changes_only_no_breaking_change():
    grouped_conv_commits = resolver.group_conv_commit_details([
        ConvCommitDetails.valid_commit("chore", datetime(2025, 10, 10, 0, 0, 0), "Very Description 01"),
        ConvCommitDetails.valid_commit("test", datetime(2025, 10, 10, 0, 0, 0), "Very Description 02"),
        ConvCommitDetails.valid_commit("docs", datetime(2025, 10, 10, 0, 0, 0), "Very Description 03"),
        ConvCommitDetails.valid_commit("build", datetime(2025, 10, 10, 0, 0, 0), "Very Description 04"),
        ConvCommitDetails.valid_commit("ops", datetime(2025, 10, 10, 0, 0, 0), "Very Description 05")
    ])

    assert not grouped_conv_commits.has_breaking_change()
    assert grouped_conv_commits.has_other_change()
    assert not grouped_conv_commits.has_feature()
    assert not grouped_conv_commits.has_fix()
    assert grouped_conv_commits.get_highest_change() == ChangeType.PATCH


def test_grouping_mixed_other_changes_only_with_breaking_change():
    grouped_conv_commits = resolver.group_conv_commit_details([
        ConvCommitDetails.valid_commit("chore", datetime(2025, 10, 10, 0, 0, 0), "Very Description 01",
                                       breaking_change=True),
        ConvCommitDetails.valid_commit("test", datetime(2025, 10, 10, 0, 0, 0), "Very Description 02")
    ])

    assert grouped_conv_commits.has_breaking_change()
    assert grouped_conv_commits.has_other_change()
    assert not grouped_conv_commits.has_feature()
    assert not grouped_conv_commits.has_fix()
    assert grouped_conv_commits.get_highest_change() == ChangeType.MAJOR


def test_grouping_mixed_everything_no_breaking_change():
    grouped_conv_commits = resolver.group_conv_commit_details([
        ConvCommitDetails.valid_commit("chore", datetime(2025, 10, 10, 0, 0, 0), "Very Description 01"),
        ConvCommitDetails.valid_commit("test", datetime(2025, 10, 10, 0, 0, 0), "Very Description 02"),
        ConvCommitDetails.valid_commit("docs", datetime(2025, 10, 10, 0, 0, 0), "Very Description 03"),
        ConvCommitDetails.valid_commit("build", datetime(2025, 10, 10, 0, 0, 0), "Very Description 04"),
        ConvCommitDetails.valid_commit("ops", datetime(2025, 10, 10, 0, 0, 0), "Very Description 05"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 06"),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 07")
    ])

    assert not grouped_conv_commits.has_breaking_change()
    assert grouped_conv_commits.has_other_change()
    assert grouped_conv_commits.has_feature()
    assert grouped_conv_commits.has_fix()
    assert grouped_conv_commits.get_highest_change() == ChangeType.MINOR


def test_grouping_mixed_everything_with_breaking_change():
    grouped_conv_commits = resolver.group_conv_commit_details([
        ConvCommitDetails.valid_commit("chore", datetime(2025, 10, 10, 0, 0, 0), "Very Description 01"),
        ConvCommitDetails.valid_commit("test", datetime(2025, 10, 10, 0, 0, 0), "Very Description 02"),
        ConvCommitDetails.valid_commit("docs", datetime(2025, 10, 10, 0, 0, 0), "Very Description 03"),
        ConvCommitDetails.valid_commit("build", datetime(2025, 10, 10, 0, 0, 0), "Very Description 04"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 05"),
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 10, 0, 0, 0), "Very Description 06",
                                       breaking_change=True),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 10, 0, 0, 0), "Very Description 07")
    ])

    assert grouped_conv_commits.has_breaking_change()
    assert grouped_conv_commits.has_other_change()
    assert grouped_conv_commits.has_feature()
    assert grouped_conv_commits.has_fix()
    assert grouped_conv_commits.get_highest_change() == ChangeType.MAJOR
