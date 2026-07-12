from datetime import datetime

from project_git_release.change_log import generate_release_log
from project_git_release.classes import GitRelease
from project_git_release.classes.conv_commit import ConvCommitDetails
from project_git_release.common import group_conv_commit_details


def test_generate_release_log_multiple_valid_commits(release_config):
    commit_details = group_conv_commit_details([
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 11, 0, 0, 0), "Very Title 01", False, None, None,
                                       None),
        ConvCommitDetails.valid_commit("chore", datetime(2025, 10, 12, 0, 0, 0), "Very Title 02", False, "Very chore",
                                       "Very scope",
                                       None),
        ConvCommitDetails.valid_commit("fix", datetime(2025, 10, 13, 0, 0, 0), "Very Title 03", False, None,
                                       "little_scope",
                                       None)
    ])

    release_log = generate_release_log(release_config,
                                       commit_details,
                                       GitRelease("0.0.1", "Release 0.0.1", "very_sha_prev"),
                                       GitRelease("0.1.0", "Release 0.1.0", "very_sha_next"))

    assert release_log == f"## [0.1.0]({release_config.git_url()}/compare/0.0.1...0.1.0) (2026-07-12)\n### Features\n*  Very Title 01\n### Bugfix(es)\n* **little_scope:** Very Title 03\n### Other changes\n* **chore(Very scope):** Very Title 02\n---\n"


def test_generate_release_log_invalid_commit(release_config):
    commit_details = group_conv_commit_details([
        ConvCommitDetails.invalid_commit(datetime(2025, 10, 11, 0, 0, 0), "Very Invalid Title")
    ])

    release_log = generate_release_log(release_config,
                                       commit_details,
                                       GitRelease("0.0.1", "Release 0.0.1", "very_sha_prev"),
                                       GitRelease("0.1.0", "Release 0.1.0", "very_sha_next"))

    assert release_log == f"## [0.1.0]({release_config.git_url()}/compare/0.0.1...0.1.0) (2026-07-12)\n### Other changes\n* Very Invalid Title\n---\n"


def test_generate_release_log_breaking_change(release_config):
    commit_details = group_conv_commit_details([
        ConvCommitDetails.valid_commit("feat", datetime(2025, 10, 11, 0, 0, 0), "Very Title 01", True, None, None,
                                       None)
    ])

    release_log = generate_release_log(release_config,
                                       commit_details,
                                       GitRelease("0.0.1", "Release 0.0.1", "very_sha_prev"),
                                       GitRelease("1.0.0", "Release 1.0.0", "very_sha_next"))

    assert release_log == f"## [1.0.0]({release_config.git_url()}/compare/0.0.1...1.0.0) (2026-07-12)\n### Breaking changes\n*  Very Title 01\n---\n"


def test_generate_release_valid_change_invalid_type(release_config):
    commit_details = group_conv_commit_details([
        ConvCommitDetails.valid_commit("invalid", datetime(2025, 10, 11, 0, 0, 0), "Very Title 01", False, None, None,
                                       None)
    ])

    release_log = generate_release_log(release_config,
                                       commit_details,
                                       GitRelease("0.0.1", "Release 0.0.1", "very_sha_prev"),
                                       GitRelease("1.0.0", "Release 1.0.0", "very_sha_next"))

    assert release_log == f"## [1.0.0]({release_config.git_url()}/compare/0.0.1...1.0.0) (2026-07-12)\n### Other changes\n* **invalid:** Very Title 01\n---\n"
