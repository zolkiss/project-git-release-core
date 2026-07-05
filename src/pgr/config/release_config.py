class ReleaseConfig:
    def __init__(self, token: str, url: str, owner: str, repo: str,
                 release_branch: str = "static--release--branch",
                 git_verbose_logging: bool = False,
                 default_branch: str = "main",
                 git_print_stdout: bool = True,
                 git_print_stderr: bool = True,
                 release_commit_message: str = "chore: Releasing version %VERSION%",
                 release_version_prefix: str = "",
                 changelog_file: str = "CHANGELOG.md",
                 version_file: str | None = "version.txt",
                 version_config_file: str = ".git-release-conf.json",
                 version_config_text_append_missing: bool = True,
                 version_config_marker: str = "x-git-release-version",
                 version_config_marker_block_start: str = "x-git-release-version-start",
                 version_config_marker_block_end: str = "x-git-release-version-end",
                 auto_delete_temp_dir: bool = True
                 ):
        self.token = token
        self.url = url
        self.owner = owner
        self.repo = repo
        self.default_branch = default_branch
        self.release_commit_message = release_commit_message
        self.release_branch = release_branch
        self.git_verbose_logging = git_verbose_logging
        self.git_print_stdout = git_print_stdout
        self.git_print_stderr = git_print_stderr
        self.release_version_prefix = release_version_prefix
        self.changelog_file = changelog_file
        self.version_file = version_file
        self.version_config_file = version_config_file
        self.version_config_marker = version_config_marker
        self.version_config_marker_block_start = version_config_marker_block_start
        self.version_config_marker_block_end = version_config_marker_block_end
        self.version_config_text_append_missing = version_config_text_append_missing
        self.auto_delete_temp_dir = auto_delete_temp_dir

    def git_url(self) -> str:
        return f"{self.url}/{self.owner}/{self.repo}"

    def git_verbose_flag(self) -> str:
        if self.git_verbose_logging:
            return "--verbose"
        else:
            return "--no-verbose"
