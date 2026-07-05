# project-git-release (WIP)

## Disclaimer

I'm not a Python developer... I'm doing this as a hobby, because I need something to create version and releases on
Gitea
for my home project on the self-hosted Gitea. Use at your own risk, the source is open. I do not take responsibility for
the
damaged caused.

## About the project

The project is heavily inspired by the [release-please](https://github.com/googleapis/release-please) project. The goal
is to provide a similar flow to collect
changes based on conventional commit messages, and handle the releases.

Since the release-please is tied to the Github, it cannot be really used for Gitea, Bitbucket, Gitlab, etc. This gave
the idea to create a library, which can be used on a modular base, and can be freely extended by You, or anyone else.

Since my use case is to release project version in self-hosted environment (Release on Gitea using Argo Workflow), I
decided to go with Python.

## Usage

### Command line

The core module has a ```__main__.py``` file, hence it can be run easily from command line. For the program argument and
options
handling I used Typer. Also, the module supports the .env based property provision. Currently, this is the parameter
resolution order:

```text
System Environment Variables -> .env file content -> Non-default options
```

During the processing just the given property is overridden, not the whole set.

The module accepts three arguments: update, release and update_and_release

- update: Collects the unreleased commits, also updates (and creates) the PR.
- release: Doing the actual release: Creates the tags, the releases, etc.
- update_and_release: The two above after each-other

While the runner supports the `--help` parameter, you can list the environments variable counterparts with the
`--list-envs` options. In both cases, the other command resolutions are stopped.

#### List of the available options and variables:

| Option                              | Env Variable                         | Description                                                                                                                                                       | Default value                        |
|:------------------------------------|:-------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| --connector                         | PGR_CONNECTOR                        | Git Connector selector. If not set, the first available will be used. If set, will throw error in case of missing connector                                       |                                      |
| --git-repo-url                      | PGR_GIT_REPO_URL                     | The repository base URL for the Git repository                                                                                                                    |                                      |
| --git-repo-owner                    | PGR_GIT_REPO_OWNER                   | The repository owner for the Git repository                                                                                                                       |                                      |
| --git-repo-name                     | PGR_GIT_REPO_NAME                    | The repository name for the Git repository                                                                                                                        |                                      |
| --default-branch                    | PGR_DEFAULT_BRANCH                   | Default branch name                                                                                                                                               | `main`                               |
| --release-branch                    | PGR_RELEASE_BRANCH                   | Name of the release branch where the version update will be generated                                                                                             | `static--release--branch`            |
| --print-git-stdout                  | PGR_PRINT_GIT_STDOUT                 | Print the standard output of Git commands                                                                                                                         | `True`                               |
| --print-git-stderr                  | PGR_PRINT_GIT_STDERR                 | Print the error output of Git commands                                                                                                                            | `True`                               |
| --release-commit-message            | PGR_RELEASE_COMMIT_MESSAGE           | The generated title of Pull Requests and Commits. Supports %VERSION% placeholder for the actual version                                                           | `chore: Releasing version %VERSION%` |
| --release-version-prefix            | PGR_RELEASE_VERSION_PREFIX           | Optional prefix for semantic versioning                                                                                                                           |                                      |
| --version-changelog-file            | PGR_VERSION_CHANGELOG_FILE           | The generated markdown changelog file                                                                                                                             | `CHANGELOG.md`                       |
| --version-file                      | PGR_VERSION_FILE                     | This file contains the version only.                                                                                                                              | `version.txt`                        |
| --version-config-file               | PGR_VERSION_CONFIG_FILE              | The configuration file used for extra files handling                                                                                                              | `.git-release-conf.json`             |
| --version-config-append-missing     | PGR_VERSION_CONFIG_APPEND_MISSING    | Controls if the missing version should be appended to the marked lines, or not                                                                                    | `True`                               |
| --version-config-marker             | PGR_VERSINO_CONFIG_MARKER            | The marker used for inline version update                                                                                                                         | `x-git-release-version`              |
| --version-config-marker-block-start | PGR_VERSIN_CONFIG_MARKER_BLOCK_START | The marker used for end of block version update. Support multiple lines, but if append is enabled, it will be appended to every line                              | `x-git-release-version-start`        |
| --version-config-marker-block-end   | PGR_VERSIN_CONFIG_MARKER_BLOCK_END   | The marker used for end of block version update. Support multiple lines, but if append is enabled, it will be appended to every line                              | `x-git-release-version-end`          |
| --auto-delete-temp-dir              | PGR_AUTO_DELETE_TEMP_DIR             | Flag to automatically remove temporary created working dir                                                                                                        | `True`                               |
| --git-token-env-var                 | PGR_GIT_TOKEN_ENV_VAR                | The environment variable which stores the token for the Git. Cannot set with git_token_file option, but one of them needs to be set. The PGR_TOKEN is the default | `PGR_TOKEN`                          |
| --git-token-file                    | PGR_GIT_TOKEN_FILE                   | The file which contains the Git token. Cannot set with git_token_env_var option, but one of them needs to be set                                                  |                                      |

#### Sample

```shell
pip install project-git-release-core project-git-release-connector-gitea

python3 -m pgr --env-file-path "[VALID_PATH_TO_DOT_ENV]" update
```

### Python code

While currently the suggested mode to use this from command line, you can invode the logic from code.
For that, a [Release Engine](src/pgr/core.py#L17) Class was created, which needs to be instantiated, and you have to
call the release or update methods.

As input parameter it excepts:

- [ReleaseConfig](src/pgr/config/release_config.py) instance
- [Connector](src/pgr/interfaces.py#L10)

#### Sample

```python
from pgr import ReleaseEngine
from pgr.config.release_config import ReleaseConfig
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

Well... I'm a Java software developer since November 2011. I worked in multiple domain (telco, retail, finance, etc.).
Technology side I started with Java EE, but went with Spring (Boot) for the last 10 Years, but I'm definitely not a
Python developer.

To implement the project, I used the Claude (Free Tier), please the [AI Disclaimer](#ai-disclaimer) for more
information.

## AI Disclaimer

As I mentioned above, I'm not a Python developer, hence I used Claude AI (Free Tier) to help in the creation of the
project.

Currently, for the project I did not generated any actual code block (as far as I remember). What I used the AI for:

* Helping in the generation of GIT commands
* Helping in the generation of Regex expression
* I asked about project structure
* I asked about Python best practices
* I used it for brainstorming
* Proofreading this README file :D

I tried to avoid to share whole project parts with AI, and I never gave access to use my project (no agentic AI was
involved)