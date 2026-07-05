import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pgr import log
from pgr.change_log import generate_change_chapters
from pgr.config.release_config import ReleaseConfig
from pgr.conv_commit import resolver
from pgr.conv_commit.resolver import GroupedConvCommits, ChangeType
from pgr.file_handler.changelog_generator import ChangelogGenerator
from pgr.file_handler.extra_file_version_updater import ExtraFileVersionUpdater
from pgr.file_handler.version_file_generator import generate_version_file
from pgr.git import GitCommander
from pgr.interfaces import Connector, CommitDetails, GitRelease, NewVersion, GitReleasePR


class ReleaseEngine:
    def __init__(self, connector_type: type[Connector], config: ReleaseConfig, auto_delete_temp_dir: bool = True):
        self.connector = connector_type(config)
        self.temp_dir = TemporaryDirectory(prefix="git-release-", delete=auto_delete_temp_dir)
        self.git = GitCommander(config, self.temp_dir.name)
        self.config = config

    def do_release(self):
        self.prepare_release_branch_locally()

        latest_release_commit = self.connector.get_latest_release()

        commit_list = self.find_commits_since_last_release(latest_release_commit)
        if len(commit_list) == 0:
            log.info("There is no commit since the latest release. Quitting...")
            exit(0)

        grouped_commits = resolver.group_conv_commit_details(resolver.resolve_commit_messages(commit_list))
        next_version = self.__calculate_next_version(grouped_commits, latest_release_commit)
        self.__update_files(grouped_commits, latest_release_commit, next_version)
        self.__force_push_changes(next_version)
        self.__update_pull_request(next_version, grouped_commits)

    def prepare_release_branch_locally(self):
        repository_cloned = self.git.clone_repository()
        if not repository_cloned:
            log.info("Cannot clone repository. Exiting...")
            exit(1)
        release_branch_exists = self.git.is_release_branch_exists()
        log.debug("Does release branch exists?: %s", release_branch_exists)
        if not release_branch_exists:
            release_branch_checkout = self.git.create_release_branch()
        else:
            release_branch_checkout = self.git.update_release_branch()
        if not release_branch_checkout:
            log.info("Error during release branch checkout...")
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
                current_version,
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

    def find_commits_since_last_release(self, latest_release_commit: GitRelease | None) -> list[CommitDetails]:
        commit_sha = None
        if latest_release_commit is not None:
            commit_sha = latest_release_commit.commit_sha

        hash_and_msg_list = self.git.get_commits_since_latest_release(commit_sha)

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

        semver_parts[highest_change] = str(int(semver_parts[highest_change]) + 1)
        return NewVersion(".".join(semver_parts), self.config.release_version_prefix)

    def __update_pull_request(self, next_version: NewVersion,
                              grouped_commits: GroupedConvCommits) -> GitReleasePR | None:
        pull_request_title = self.config.release_commit_message.replace("%VERSION%", next_version.get_full_version())
        pull_request_commit_text = self.__generate_commit_text(next_version, grouped_commits)

        latest_release_pr = self.connector.get_latest_open_release_pr()
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
