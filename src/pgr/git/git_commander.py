import subprocess

from pgr import log
from pgr.config.release_config import ReleaseConfig
from pgr.git.data_classes import GitCmdResult, GitHashAndMsg

COMMIT_SEPARATOR = "|"


class GitCommander:
    def __init__(self, config: ReleaseConfig, temp_dir: str):
        self.config = config
        self.repository_cloned = False
        self.temp_dir = temp_dir
        log.info("Temp DIR is created at: %s", temp_dir)

    @staticmethod
    def __log_command(command: list[str]):
        log.debug("Running command: '%s'", ' '.join(command))

    def __log_git_stdout(self, stdout: str):
        if self.config.git_print_stdout and stdout != "":
            log.info(f"\n{stdout}")

    def __run_git_command(self, command: list[str],
                          error_msg: str = "Error while running command: %s",
                          run_in_temp: bool = True,
                          skip_error_for_exit_code: list[int] | None = None) -> GitCmdResult:
        try:
            if run_in_temp:
                base_dir = self.temp_dir
            else:
                base_dir = None
            result = subprocess.run(command, cwd=base_dir, check=True, capture_output=True, text=True)
            self.__log_git_stdout(result.stdout)
            return GitCmdResult(True, result.stdout, result.stderr, result.returncode)
        except subprocess.CalledProcessError as e:
            self.__log_git_stdout(e.stdout)
            if skip_error_for_exit_code is None or e.returncode not in skip_error_for_exit_code:
                log.error(error_msg)
                if self.config.git_print_stderr:
                    log.error(f"\n{e.stderr}")
            return GitCmdResult(False, e.stdout, e.stderr, e.returncode)

    def clone_repository(self) -> bool:
        command = ["git", "clone", self.config.git_url(), self.temp_dir,
                   self.config.git_verbose_flag()]
        self.__log_command(command)
        return self.__run_git_command(command, "Error while cloning repository: %s", False).result

    def is_release_branch_exists(self) -> bool:
        command = ["git", "ls-remote", "--exit-code", "origin",
                   self.config.release_branch]
        self.__log_command(command)
        return self.__run_git_command(command=command,
                                      error_msg="Error while getting release branch information",
                                      skip_error_for_exit_code=[2]).result

    def create_release_branch(self) -> bool:
        command = ["git", "checkout", "-b", self.config.release_branch]
        self.__log_command(command)
        return self.__run_git_command(command, "Error while creating release branch from latest commit").result

    def update_release_branch(self) -> bool:
        command = ["git", "fetch", "origin", f"{self.config.release_branch}:{self.config.release_branch}"]
        self.__log_command(command)
        if not self.__run_git_command(command, f"Error wile fetchin origin/{self.config.release_branch}"):
            return False

        command = ["git", "checkout", self.config.release_branch]
        self.__log_command(command)
        branch_checked_out = self.__run_git_command(command, "Error while checking out existing release branch")
        if not branch_checked_out:
            return False

        command = ["git", "reset", "--hard", f"origin/{self.config.default_branch}"]
        self.__log_command(command)
        return self.__run_git_command(command,
                                      f"Error while resetting branch to {self.config.default_branch}").result

    def add_untracked_files(self) -> bool:
        command = ["git", "ls-files", "-o", "-m", "-d"]
        self.__log_command(command)
        files_listed = self.__run_git_command(command,
                                              "Error while listing untracked files")
        if not files_listed.result:
            return False

        all_files_added = True
        for file in files_listed.stdout.splitlines():
            command = ["git", "add", file]
            self.__log_command(command)
            git_add_result = self.__run_git_command(command, f"Error while adding {file} to git")
            all_files_added = all_files_added and git_add_result.result

        command = ["git", "ls-files", "-o", "-m", "-d"]
        self.__log_command(command)
        all_files_added = self.__run_git_command(command,
                                                 "Error while listing untracked files")

        return all_files_added.stdout == ""

    def commit_and_force_push_tracked_changes(self, next_full_version: str) -> bool:
        command = ["git", "commit", "-m",
                   self.config.release_commit_message.replace("%VERSION%", next_full_version)]
        self.__log_command(command)
        files_commited = self.__run_git_command(command,
                                                "Error while commiting files")
        if not files_commited.result:
            return False

        command = ["git", "push", "--porcelain", "--force", "origin", self.config.release_branch]
        self.__log_command(command)
        force_push = self.__run_git_command(command, "Error while force pushing changes")
        return force_push.result

    def get_commits_since_latest_release(self, latest_release_commit: str | None) -> list[GitHashAndMsg]:
        since_text = f"origin/{self.config.default_branch}"
        if latest_release_commit is not None:
            since_text = f"{latest_release_commit}..{since_text}"

        command = ["git", "log", "origin", "--reverse", f"--pretty=%H{COMMIT_SEPARATOR}%s", since_text]
        self.__log_command(command)
        commits = self.__run_git_command(command, f"Error while getting for {since_text}")
        if not commits.result:
            exit(1)

        return_list = []
        for commit in commits.stdout.splitlines():
            parts = commit.split(COMMIT_SEPARATOR)
            return_list.append(GitHashAndMsg(hash=parts[0], message=parts[1]))
        return return_list
