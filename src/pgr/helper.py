from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar('T')


@dataclass(frozen=True)
class RunnerHelperData(Generic[T]):
    env_name: str
    help_text: str
    default: T | None = None


@dataclass(frozen=True)
class RunnerHelper:
    connector: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_CONNECTOR",
                                                 "Git Connector selector. If not set, the first available will be used. If set, will throw error in case of missing connector",
                                                 ""))
    git_repo_url: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_GIT_REPO_URL",
                                                 "The repository base URL for the Git repository",
                                                 ""))
    git_repo_owner: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_GIT_REPO_OWNER",
                                                 "The repository owner for the Git repository",
                                                 ""))
    git_repo_name: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_GIT_REPO_NAME",
                                                 "The repository name for the Git repository",
                                                 ""))
    default_branch: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_DEFAULT_BRANCH",
                                                 "Default branch name",
                                                 "main"))
    release_branch: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_RELEASE_BRANCH",
                                                 "Name of the release branch where the version update will be generated",
                                                 "static--release--branch"))
    print_git_stdout: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_PRINT_GIT_STDOUT",
                                                 "Print the standard output of Git commands",
                                                 True))
    print_git_stderr: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_PRINT_GIT_STDERR",
                                                 "Print the error output of Git commands",
                                                 True))
    release_commit_message: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_RELEASE_COMMIT_MESSAGE",
                                                 "The generated title of Pull Requests and Commits. Supports %VERSION% placeholder for the actual version",
                                                 "chore: Releasing version %VERSION%"))
    release_version_prefix: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_RELEASE_VERSION_PREFIX",
                                                 "Optional prefix for semantic versioning",
                                                 ""))
    version_changelog_file: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSION_CHANGELOG_FILE",
                                                 "The generated markdown changelog file",
                                                 "CHANGELOG.md"))
    version_file: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSION_FILE",
                                                 "This file contains the version only.",
                                                 "version.txt"))
    version_config_file: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSION_CONFIG_FILE",
                                                 "The configuration file used for extra files handling",
                                                 ".git-release-conf.json"))
    version_config_append_missing: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSION_CONFIG_APPEND_MISSING",
                                                 "Controls if the missing version should be appended to the marked lines, or not",
                                                 True))
    version_config_marker: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSINO_CONFIG_MARKER",
                                                 "The marker used for inline version update",
                                                 "x-git-release-version"))
    version_config_marker_block_start: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSIN_CONFIG_MARKER_BLOCK_START",
                                                 "The marker used for end of block version update. Support multiple lines, but if append is enabled, it will be appended to every line",
                                                 "x-git-release-version-start"))
    version_config_marker_block_end: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_VERSIN_CONFIG_MARKER_BLOCK_END",
                                                 "The marker used for end of block version update. Support multiple lines, but if append is enabled, it will be appended to every line",
                                                 "x-git-release-version-end"))
    auto_delete_temp_dir: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_AUTO_DELETE_TEMP_DIR",
                                                 "Flag to automatically remove temporary created working dir",
                                                 True))
    git_token_env_var: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_GIT_TOKEN_ENV_VAR",
                                                 "The environment variable which stores the token for the Git. Cannot set with git_token_file option, but one of them needs to be set. The PGR_TOKEN is the default",
                                                 "PGR_TOKEN"))
    git_token_file: RunnerHelperData[str] = field(
        default_factory=lambda: RunnerHelperData("PGR_GIT_TOKEN_FILE",
                                                 "The file which contains the Git token. Cannot set with git_token_env_var option, but one of them needs to be set",
                                                 ""))


runner_config = RunnerHelper()
