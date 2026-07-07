# project-git-release (WIP)

## General Disclaimer

I'm not a Python developer... I'm doing this as a hobby, because I need something to create versions and releases on
Gitea for my home project on self-hosted Gitea. Use at your own risk, the source is open. I do not take
responsibility for any damage caused.

## About the project

The project is heavily inspired by the [release-please](https://github.com/googleapis/release-please) project. The
goal is to provide a similar flow for collecting changes based on conventional commit messages and handling
releases.

Since release-please is tied to GitHub, it cannot really be used for Gitea, Bitbucket, GitLab, etc. This led to the
idea of creating a library that can be used in a modular way, and can be freely extended by you or anyone else.

Since my use case is to release project versions in a self-hosted environment (releasing on Gitea using Argo
Workflow), I decided to go with Python.

## Usage

### Command line

The core module has a ```__main__.py``` file, hence it can be run easily from the command line. For program
argument and options handling I used Typer. Also, the module supports .env-based property provision. Currently,
this is the parameter resolution order:

```text
System Environment Variables -> .env file content -> Non-default options
```

During processing, only the given property is overridden, not the whole set.

The module accepts three arguments: update, release and update_and_release

- update: Collects the unreleased commits, and also updates (and creates) the PR.
- release: Performs the actual release: creates the tags, the releases, etc.
- update_and_release: Runs the two above, one after the other

While the runner supports the `--help` parameter, you can list the environment variable counterparts with the
`--list-envs` option. In both cases, further command resolution is stopped.

#### List of the available options and variables:

| Option                              | Env Variable                         | Description                                                                                                                                                       | Default value                      |
|:------------------------------------|:-------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|
| --connector                         | PGR_CONNECTOR                        | Git Connector selector. If not set, the first available will be used. If set, will throw error in case of missing connector                                       |                                    |
| --git-repo-url                      | PGR_GIT_REPO_URL                     | The repository base URL for the Git repository                                                                                                                    |                                    |
| --git-repo-owner                    | PGR_GIT_REPO_OWNER                   | The repository owner for the Git repository                                                                                                                       |                                    |
| --git-repo-name                     | PGR_GIT_REPO_NAME                    | The repository name for the Git repository                                                                                                                        |                                    |
| --default-branch                    | PGR_DEFAULT_BRANCH                   | Default branch name                                                                                                                                               | `main`                             |
| --release-branch                    | PGR_RELEASE_BRANCH                   | Name of the release branch where the version update will be generated                                                                                             | `static--release--branch`          |
| --print-git-stdout                  | PGR_PRINT_GIT_STDOUT                 | Print the standard output of Git commands                                                                                                                         | `True`                             |
| --print-git-stderr                  | PGR_PRINT_GIT_STDERR                 | Print the error output of Git commands                                                                                                                            | `True`                             |
| --release-commit-message            | PGR_RELEASE_COMMIT_MESSAGE           | The generated title of Pull Requests and Commits. Supports %VERSION% placeholder for the actual version                                                           | `chore: Release version %VERSION%` |
| --release-version-prefix            | PGR_RELEASE_VERSION_PREFIX           | Optional prefix for semantic versioning                                                                                                                           |                                    |
| --version-changelog-file            | PGR_VERSION_CHANGELOG_FILE           | The generated markdown changelog file                                                                                                                             | `CHANGELOG.md`                     |
| --version-file                      | PGR_VERSION_FILE                     | This file contains the version only.                                                                                                                              | `version.txt`                      |
| --version-config-file               | PGR_VERSION_CONFIG_FILE              | The configuration file used for extra files handling                                                                                                              | `.git-release-conf.json`           |
| --version-config-append-missing     | PGR_VERSION_CONFIG_APPEND_MISSING    | Controls if the missing version should be appended to the marked lines, or not                                                                                    | `True`                             |
| --version-config-marker             | PGR_VERSINO_CONFIG_MARKER            | The marker used for inline version update                                                                                                                         | `x-git-release-version`            |
| --version-config-marker-block-start | PGR_VERSIN_CONFIG_MARKER_BLOCK_START | The marker used for end of block version update. Support multiple lines, but if append is enabled, it will be appended to every line                              | `x-git-release-version-start`      |
| --version-config-marker-block-end   | PGR_VERSIN_CONFIG_MARKER_BLOCK_END   | The marker used for end of block version update. Support multiple lines, but if append is enabled, it will be appended to every line                              | `x-git-release-version-end`        |
| --auto-delete-temp-dir              | PGR_AUTO_DELETE_TEMP_DIR             | Flag to automatically remove temporary created working dir                                                                                                        | `True`                             |
| --git-token-env-var                 | PGR_GIT_TOKEN_ENV_VAR                | The environment variable which stores the token for the Git. Cannot set with git_token_file option, but one of them needs to be set. The PGR_TOKEN is the default | `PGR_TOKEN`                        |
| --git-token-file                    | PGR_GIT_TOKEN_FILE                   | The file which contains the Git token. Cannot set with git_token_env_var option, but one of them needs to be set                                                  |                                    |

#### Sample

```shell
pip install project-git-release-core project-git-release-connector-gitea

python3 -m pgr --env-file-path "[VALID_PATH_TO_DOT_ENV]" update
```

### Python code

While currently the suggested mode is to use this from the command line, you can invoke the logic from code.
For that, a [Release Engine](src/pgr/core.py#L17) Class was created, which needs to be instantiated; you then call
the release or update methods.

As input parameters, it accepts:

- [ReleaseConfig](src/pgr/core/release_config.py) instance
- [Connector](src/pgr/core/connector.py#L18)

#### Sample

```python
from pgr import ReleaseEngine
from pgr.core.release_config import ReleaseConfig
from pgr.registry import get_connector

token = "VERY_SECRET_TOKEN_VALUE"
url = "https://github.com"
owner = "RepoOwner"
repo = "TheRepositoryName"

config = ReleaseConfig(token, url, owner, repo,
                       release_branch="static-release-branch",
                       git_verbose_logging=True,
                       release_version_prefix="v")

connector = get_connector("gitea")
engine = ReleaseEngine(connector, config, auto_delete_temp_dir=False)
engine.update_version()
```
## About the author

I've been a Java software developer since November 2011. I've worked in multiple domains (telco, retail, finance,
etc.). On the technology side, I started with Java EE, but have used Spring (Boot) for the last 10 years, though I'm
definitely not a Python developer.

To implement the project, I used Claude (Free Tier); please see the [AI Disclaimer](#ai-disclaimer) below for more
information.

## AI Disclaimer

As I mentioned above, I'm not a Python developer, hence I used Claude AI (Free Tier) to help in the creation of the
project.

Currently, for the project I did not generated any actual code blocks for this project (as far as I remember). What I
used AI for:

* Helping generate Git commands
* Helping generate regex expressions
* Asking about project structure
* Asking about Python best practices
* Brainstorming
* Proofreading this README file :D

I tried to avoid sharing whole project parts with the AI, and never gave it access to my project (no agentic AI was
involved).