import json
from pathlib import Path
from tempfile import TemporaryDirectory

from project_git_release import log
from project_git_release.change_log import generate_change_chapters, generate_release_log
from project_git_release.classes import CommitDetails, GitRelease, NewVersion, GitReleasePR
from project_git_release.classes.conv_commit import GroupedConvCommits, ChangeType
from project_git_release.classes.version_parts import VersionParts
from project_git_release.common import resolve_commit_messages, group_conv_commit_details, build_version_regex
from project_git_release.common.changelog_generator import ChangelogGenerator
from project_git_release.core import Connector
from project_git_release.core.release_config import ReleaseConfig
from project_git_release.file.extra_file_version_updater import ExtraFileVersionUpdater
from project_git_release.file.version_file_generator import generate_version_file
from project_git_release.git import GitCommander


class ReleaseEngine:
    def __init__(self, connector_type: type[Connector], config: ReleaseConfig, auto_delete_temp_dir: bool = True):
        self.connector = connector_type(config)
        self.temp_dir = TemporaryDirectory(prefix="git-release-", delete=auto_delete_temp_dir)
        self.git = GitCommander(config, self.temp_dir.name)
        self.config = config

    def update_version(self):
        self.__prepare_release_branch_locally()

        latest_release_commit = self.connector.get_latest_release()
        latest_unreleased_commit = self.__find_latest_unreleased_version(latest_release_commit)

        actual_commit = latest_release_commit
        if latest_unreleased_commit is not None:
            actual_commit = latest_unreleased_commit

        commit_list = self.__find_commits_since_last_release(actual_commit)
        if len(commit_list) == 0:
            log.info("There is no commit since the latest release. Quitting...")
            exit(0)

        grouped_commits = group_conv_commit_details(resolve_commit_messages(commit_list))
        next_version = self.__calculate_next_version(grouped_commits, actual_commit)
        self.__update_files(grouped_commits, actual_commit, next_version)
        self.__force_push_changes(next_version)
        self.__update_pull_request(next_version, grouped_commits)

    def release_unreleased_prs(self):
        self.__checkout_default_branch()
        latest_release = self.connector.get_latest_release()
        unreleased_versions = self.__find_latest_unreleased_versions(latest_release)

        reverse_unreleased_versions = list(reversed(unreleased_versions))
        if len(unreleased_versions) == 0:
            log.info("Cannot find unreleased merged PR")
            return
        else:
            for idx, unreleased_version in enumerate(reverse_unreleased_versions):
                log.info("Unreleased chore PR: %s ('%s', %s)", unreleased_version.tag_name,
                         unreleased_version.tag_message,
                         unreleased_version.commit_sha)
                if idx == 0:
                    previous_release = latest_release
                else:
                    previous_release = reverse_unreleased_versions[idx - 1]
                commit_list = self.__find_commits_since_last_release(previous_release,
                                                                     unreleased_version)
                if len(commit_list) == 0:
                    log.info("There is no commit since the latest release. Quitting...")
                    exit(0)
                commits_without_release = [commit for commit in commit_list if
                                           commit.hash != unreleased_version.commit_sha]
                grouped_commits = group_conv_commit_details(resolve_commit_messages(commits_without_release))
                change_log = generate_release_log(grouped_commits, previous_release, unreleased_version)
                log.info("Generated changelog for release:\n%s", change_log)

                response = self.connector.create_release(unreleased_version, change_log)
                log.info("Release is created with response:\n%s", response)

    def __find_latest_unreleased_version(self, latest_release: GitRelease | None) -> GitRelease | None:
        commits = self.__find_latest_unreleased_versions(latest_release)
        if len(commits) == 0:
            return None
        else:
            return commits[0]

    def __find_latest_unreleased_versions(self, latest_release: GitRelease | None) -> list[GitRelease]:
        commits = self.git.get_file_history(f"{self.config.version_file}", False)

        pattern = build_version_regex(self.config.release_version_prefix)
        unreleased_versions = []
        for commit in commits:
            if latest_release is not None and commit.sha == latest_release.commit_sha:
                log.info(f"Found previous release, stopping unreleased commit searching")
                break

            search_result = pattern.search(commit.message)
            if search_result is not None:
                version = search_result.group(VersionParts.FULL_VERSION)
                log.info(f"Found latest unreleased version: {commit.message} ({commit.sha})")
                unreleased_versions.append(GitRelease(version, commit.message, commit.sha))

        return unreleased_versions

    def __get_latest_unreleased_version(self) -> GitRelease | None:
        closed_release_prs = self.connector.get_latest_release_prs("closed")
        latest_merged_release_pr = None
        version = None
        for pr in closed_release_prs:
            if pr.merged:
                version_pattern = build_version_regex(self.config.release_version_prefix)
                match = version_pattern.search(pr.title)
                if match is None:
                    log.warn("The merged PR (%s) does not have version information", pr.title)
                    continue
                else:
                    version = match.group(VersionParts.FULL_VERSION)
                    latest_merged_release_pr = pr
                    break

        if latest_merged_release_pr is None or version is None:
            log.warn("Couldn't find a not merged closed release PR in the PR history.")
            return None

        tag_details = self.connector.get_release_by_tag(version)
        if tag_details is not None:
            return None

        return GitRelease(version, latest_merged_release_pr.title, latest_merged_release_pr.commit_sha)

    def __prepare_release_branch_locally(self):
        self.__checkout_default_branch()
        release_branch_exists = self.git.is_release_branch_exists()
        log.debug("Does release branch exists?: %s", release_branch_exists)
        if not release_branch_exists:
            release_branch_checkout = self.git.create_release_branch()
        else:
            release_branch_checkout = self.git.update_release_branch()
        if not release_branch_checkout:
            log.info("Error during release branch checkout...")
            exit(1)

    def __checkout_default_branch(self):
        repository_cloned = self.git.clone_repository()
        if not repository_cloned:
            log.info("Cannot clone repository. Exiting...")
            exit(1)

    def __update_files(self, grouped_commits: GroupedConvCommits, git_release: GitRelease | None,
                       next_version: NewVersion):
        if git_release is None:
            current_version = None
        else:
            current_version = git_release.tag_name

        ChangelogGenerator(self.config, self.temp_dir).generate_changelog(grouped_commits, current_version,
                                                                          next_version)
        generate_version_file(self.temp_dir, self.config, next_version)
        config_from_repo = self.__open_config_file()
        if "extra_files" in config_from_repo.keys() and config_from_repo["extra_files"] is not None:
            ExtraFileVersionUpdater(self.config, config_from_repo["extra_files"], self.temp_dir).update_files(
                next_version,
                self.config.version_config_text_append_missing)

    def __force_push_changes(self, next_version: NewVersion):
        no_untracked_files_left = self.git.add_untracked_files()
        if not no_untracked_files_left:
            log.error("Couldn't add all the untracked files to Git. Please check the logs.")
            exit(1)

        force_push_result = self.git.commit_and_force_push_tracked_changes(next_version.get_full_version())
        if not force_push_result:
            log.error("Couldn't force-push the changes. Please check the logs.")
            exit(1)

    def __find_commits_since_last_release(self, latest_release_commit: GitRelease | None,
                                          hash_until: GitRelease | None = None) -> \
            list[CommitDetails]:
        commit_sha = None
        if latest_release_commit is not None:
            commit_sha = latest_release_commit.commit_sha

        hash_until_sha = None
        if hash_until is not None:
            hash_until_sha = hash_until.commit_sha

        hash_and_msg_list = self.git.get_commits_since_latest_release(commit_sha, hash_until_sha)

        return [
            details
            for hash_and_msg in hash_and_msg_list if (details := self.__get_commit_details(hash_and_msg)) is not None
        ]

    def __get_commit_details(self, hash_and_msg):
        details = self.connector.get_commit_details(hash_and_msg)
        if details is None:
            log.warning("Couldn't find details for %s", hash_and_msg)
        return details

    def __open_config_file(self) -> dict:
        config_file_path = Path(f"{self.temp_dir.name}/{self.config.version_config_file}")
        if not config_file_path.exists():
            log.info("Cannot find extra file config")
            return dict()

        with open(config_file_path, "r") as f:
            config = json.load(f)

        return config

    def __calculate_next_version(self, grouped_commits: GroupedConvCommits,
                                 latest_release_commit: GitRelease | None) -> NewVersion:
        if latest_release_commit is None:
            semver = "0.0.0"
        else:
            semver = latest_release_commit.tag_name.lstrip(self.config.release_version_prefix)

        semver_parts = semver.split(".")
        if len(semver_parts) != 3:
            log.error("Error while calculating next version. SemVer format is wrong: {}", semver)
            exit(1)

        highest_change: ChangeType = grouped_commits.get_highest_change()
        if highest_change == ChangeType.NONE:
            log.info("No version change is calculated. Returning the input version: {}", GitRelease.tag_name)
            return NewVersion(GitRelease.tag_name, "")

        if highest_change == ChangeType.MAJOR:
            semver_parts[0] = str(int(semver_parts[0]) + 1)
            semver_parts[1] = "0"
            semver_parts[2] = "0"
        elif highest_change == ChangeType.MINOR:
            semver_parts[1] = str(int(semver_parts[1]) + 1)
            semver_parts[2] = "0"
        else:
            semver_parts[2] = str(int(semver_parts[2]) + 1)

        return NewVersion(".".join(semver_parts), self.config.release_version_prefix)

    def __update_pull_request(self, next_version: NewVersion,
                              grouped_commits: GroupedConvCommits) -> GitReleasePR | None:
        pull_request_title = self.config.release_commit_message.replace("%VERSION%", next_version.get_full_version())
        pull_request_commit_text = self.__generate_commit_text(next_version, grouped_commits)

        latest_release_pr = self.connector.get_latest_release_pr("open")
        if latest_release_pr is None:
            latest_release_pr = self.connector.create_release_pr(pull_request_title, pull_request_commit_text)
        else:
            latest_release_pr = self.connector.update_release_pr(latest_release_pr.number, pull_request_title,
                                                                 pull_request_commit_text)
        return latest_release_pr

    @staticmethod
    def __generate_commit_text(next_version: NewVersion, grouped_commits: GroupedConvCommits) -> str:
        content = [f"# ⚙️Preparing release {next_version.get_full_version()}🔨"]
        if grouped_commits.has_breaking_change():
            chapters = generate_change_chapters("Breaking changes ⛓️‍💥", [grouped_commits.braking_changes])
            content.append("")
            content.extend(chapters)
        if grouped_commits.has_feature():
            chapters = generate_change_chapters("Features 🔩", [grouped_commits.get_features()])
            content.append("")
            content.extend(chapters)
        if grouped_commits.has_fix():
            chapters = generate_change_chapters("Bugfix(es) 🩹", [grouped_commits.get_fixes()])
            content.append("")
            content.extend(chapters)
        if grouped_commits.has_other_change():
            chapters = generate_change_chapters("Other changes ❓",
                                                [grouped_commits.get_other_changes(), grouped_commits.invalid_commits],
                                                True)
            content.append("")
            content.extend(chapters)
        content.append("---")
        content.append("Generated by project-git-release")
        return "\n".join(content)
