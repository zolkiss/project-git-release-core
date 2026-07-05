import os
from importlib.metadata import entry_points
from pathlib import Path
from typing import Annotated, cast, TypeVar

import typer
from typer._click.core import ParameterSource

from pgr import log
from pgr.config import ReleaseConfig
from pgr.helper import runner_config

app = typer.Typer()

_DEFAULT_ENV_FILE_PATH = Path(".env")
_ENV_KEY_PREFIX = "PGR_"
_T = TypeVar("_T")


def _list_env_vars(value: bool) -> None:
    if not value:
        return
    typer.echo("Available PGR_* environment variables:\n")
    typer.echo(f"\t{runner_config.connector.env_name}\n\t\t{runner_config.connector.help_text}")
    typer.echo(f"\t{runner_config.git_repo_url.env_name}\n\t\t{runner_config.git_repo_url.help_text}")
    typer.echo(f"\t{runner_config.git_repo_owner.env_name}\n\t\t{runner_config.git_repo_owner.help_text}")
    typer.echo(f"\t{runner_config.git_repo_name.env_name}\n\t\t{runner_config.git_repo_name.help_text}")
    typer.echo(f"\t{runner_config.default_branch.env_name}\n\t\t{runner_config.default_branch.help_text}")
    typer.echo(f"\t{runner_config.release_branch.env_name}\n\t\t{runner_config.release_branch.help_text}")
    typer.echo(
        f"\t{runner_config.release_version_prefix.env_name}\n\t\t{runner_config.release_version_prefix.help_text}")
    typer.echo(
        f"\t{runner_config.release_commit_message.env_name}\n\t\t{runner_config.release_commit_message.help_text}")
    typer.echo(f"\t{runner_config.print_git_stdout.env_name}\n\t\t{runner_config.print_git_stdout.help_text}")
    typer.echo(f"\t{runner_config.print_git_stderr.env_name}\n\t\t{runner_config.print_git_stderr.help_text}")
    typer.echo(
        f"\t{runner_config.version_changelog_file.env_name}\n\t\t{runner_config.version_changelog_file.help_text}")
    typer.echo(f"\t{runner_config.version_file.env_name}\n\t\t{runner_config.version_file.help_text}")
    typer.echo(f"\t{runner_config.version_config_file.env_name}\n\t\t{runner_config.version_config_file.help_text}")
    typer.echo(
        f"\t{runner_config.version_config_append_missing.env_name}\n\t\t{runner_config.version_config_append_missing.help_text}")
    typer.echo(f"\t{runner_config.version_config_marker.env_name}\n\t\t{runner_config.version_config_marker.help_text}")
    typer.echo(
        f"\t{runner_config.version_config_marker_block_start.env_name}\n\t\t{runner_config.version_config_marker_block_start.help_text}")
    typer.echo(
        f"\t{runner_config.version_config_marker_block_end.env_name}\n\t\t{runner_config.version_config_marker_block_end.help_text}")
    typer.echo(f"\t{runner_config.git_token_env_var.env_name}\n\t\t{runner_config.git_token_env_var.help_text}")
    typer.echo(f"\t{runner_config.git_token_file.env_name}\n\t\t{runner_config.git_token_file.help_text}")
    typer.echo(f"\t{runner_config.auto_delete_temp_dir.env_name}\n\t\t{runner_config.auto_delete_temp_dir.help_text}")
    # add more as needed
    raise typer.Exit()


def _read_env_and_env_file(env_file_path: Path) -> dict:
    if env_file_path != _DEFAULT_ENV_FILE_PATH and (not env_file_path.exists() or not env_file_path.is_file()):
        log.error("Cannot find environment file on path %s", env_file_path)
        exit(1)
    env_variables = dict()
    for key in os.environ.keys():
        if key.startswith(_ENV_KEY_PREFIX):
            env_variables[key] = os.environ[key]

    if env_file_path.exists() and env_file_path.is_file():
        with open(env_file_path, "r") as fr:
            read_lines = fr.readlines()
            for line in read_lines:
                if line.startswith(_ENV_KEY_PREFIX):
                    sep_idx = line.index("=")
                    env_variables[line[:sep_idx]] = line[sep_idx + 1:].strip()

    return env_variables


def _resolve_env_and_cli_options(ctx: typer.Context, merged_envs: dict, env_key: str, cli_prop: str) -> _T:
    cli_value_source = ctx.get_parameter_source(cli_prop)
    if env_key in merged_envs:
        if cli_value_source == ParameterSource.DEFAULT:
            return merged_envs[env_key]

    return cast(_T, ctx.params[cli_prop])


def _resolve_git_token(ctx: typer.Context, config_from_envs: dict, git_env_token_key: str,
                       git_file_token_key: str) -> str:
    is_env_token_default = ctx.get_parameter_source(git_env_token_key) == ParameterSource.DEFAULT
    is_env_file_default = ctx.get_parameter_source(git_file_token_key) == ParameterSource.DEFAULT

    if not is_env_token_default and not is_env_file_default:
        raise typer.BadParameter(
            f"Invalid configuration. --git-token-env-var and --git-token-file cannot be used in the same time",
            ctx=ctx
        )

    if is_env_file_default:
        git_token_env = ctx.params[git_env_token_key]
        if git_token_env in config_from_envs.keys():
            return config_from_envs[git_token_env]
        else:
            raise typer.BadParameter(
                f"Cannot find {git_token_env} in the environment variables",
                ctx=ctx,
                param_hint="--git-token-env-var"
            )
    else:
        git_file_path = Path(ctx.params[git_file_token_key])
        if not git_file_path.exists() or not git_file_path.is_file():
            raise typer.BadParameter(
                f"Cannot find {git_file_path}, or it is not a file",
                ctx=ctx,
                param_hint="--git-token-file"
            )
        else:
            with open(git_file_path, "r") as fr:
                token_lines = fr.readlines()
                if len(token_lines) == 0:
                    raise typer.BadParameter(
                        f"The token file {git_file_path} is empty",
                        ctx=ctx,
                        param_hint="--git-token-file"
                    )
                else:
                    return token_lines[0]


def _resolve_connector(ctx: typer.Context, name: str):
    eps = entry_points(group="pgr.connectors")
    if len(eps) == 0:
        raise ValueError("No connectors are available.")

    if name == "":
        for ep in eps:
            log.info("No connector selected manually. Using the first one: %s", ep.name)
            return ep.load()
        raise ValueError("No connectors are available.")
    else:
        matches = [ep for ep in eps if ep.name == name]
        if not matches:
            raise typer.BadParameter(
                f"Invalid connector is set: {name}",
                ctx=ctx,
                param_hint="--connector"
            )
        return matches[0].load()


def _validate_git_repo_properties(ctx: typer.Context, merged_envs: dict):
    repo_url = _resolve_env_and_cli_options(ctx, merged_envs, runner_config.git_repo_url.env_name, "git_repo_url")
    repo_owner = _resolve_env_and_cli_options(ctx, merged_envs, runner_config.git_repo_owner.env_name, "git_repo_owner")
    repo_name = _resolve_env_and_cli_options(ctx, merged_envs, runner_config.git_repo_name.env_name, "git_repo_name")

    if repo_url == "" or repo_owner == "" or repo_name == "":
        raise typer.BadParameter(
            f"Invalid repo configuration. The git-repo-url, git-repo-owner and git-repo-name needs to be set via options or env variables",
            ctx=ctx
        )


@app.command()
def run(
        ctx: typer.Context,
        list_env: Annotated[bool,
        typer.Option(
            help="Lists the available environment variables, which are usable both as OS Envs and int .env files)",
            is_eager=True,
            callback=_list_env_vars
        )] = False,
        env_file_path: Annotated[Path,
        typer.Option(
            help="Path to the files which contains the PGR_* environment variables.\nThese values are overwriting the OS environment values"
        )] = Path(".env"),
        connector: Annotated[
            str, typer.Option(help=runner_config.connector.help_text)] = runner_config.connector.default,
        git_repo_url: Annotated[
            str, typer.Option(help=runner_config.git_repo_url.help_text)] = runner_config.git_repo_url.default,
        git_repo_owner: Annotated[
            str, typer.Option(help=runner_config.git_repo_owner.help_text)] = runner_config.git_repo_owner.default,
        git_repo_name: Annotated[
            str, typer.Option(help=runner_config.git_repo_name.help_text)] = runner_config.git_repo_name.default,
        default_branch: Annotated[
            str, typer.Option(help=runner_config.default_branch.help_text)] = runner_config.default_branch.default,
        release_branch: Annotated[
            str, typer.Option(help=runner_config.release_branch.help_text)] = runner_config.release_branch.default,
        print_git_stdout: Annotated[
            str, typer.Option(help=runner_config.print_git_stdout.help_text)] = runner_config.print_git_stdout.default,
        print_git_stderr: Annotated[
            str, typer.Option(help=runner_config.print_git_stderr.help_text)] = runner_config.print_git_stderr.default,
        release_commit_message: Annotated[
            str, typer.Option(
                help=runner_config.release_commit_message.help_text)] = runner_config.release_commit_message.default,
        release_version_prefix: Annotated[
            str, typer.Option(
                help=runner_config.release_version_prefix.help_text)] = runner_config.release_version_prefix.default,
        version_changelog_file: Annotated[
            str, typer.Option(
                help=runner_config.version_changelog_file.help_text)] = runner_config.version_changelog_file.default,
        version_file: Annotated[
            str, typer.Option(help=runner_config.version_file.help_text)] = runner_config.version_file.default,
        version_config_file: Annotated[
            str, typer.Option(
                help=runner_config.version_config_file.help_text)] = runner_config.version_config_file.default,
        version_config_append_missing: Annotated[
            str, typer.Option(
                help=runner_config.version_config_append_missing.help_text)] = runner_config.version_config_append_missing.default,
        version_config_marker: Annotated[
            str, typer.Option(
                help=runner_config.version_config_marker.help_text)] = runner_config.version_config_marker.default,
        version_config_marker_block_start: Annotated[
            str, typer.Option(
                help=runner_config.version_config_marker_block_start.help_text)] = runner_config.version_config_marker_block_start.default,
        version_config_marker_block_end: Annotated[
            str, typer.Option(
                help=runner_config.version_config_marker_block_end.help_text)] = runner_config.version_config_marker_block_end.default,
        auto_delete_temp_dir: Annotated[
            str, typer.Option(
                help=runner_config.auto_delete_temp_dir.help_text)] = runner_config.auto_delete_temp_dir.default,
        git_token_env_var: Annotated[
            str, typer.Option(
                help=runner_config.git_token_env_var.help_text)] = runner_config.git_token_env_var.default,
        git_token_file: Annotated[
            str, typer.Option(help=runner_config.git_token_file.help_text)] = runner_config.git_token_file.default
) -> None:
    config_from_envs = _read_env_and_env_file(env_file_path)
    _validate_git_repo_properties(ctx, config_from_envs)
    token = _resolve_git_token(ctx, config_from_envs, "git_token_env_var", "git_token_file")
    connector_name = _resolve_env_and_cli_options(ctx, config_from_envs, runner_config.connector.env_name, "connector")
    connector = _resolve_connector(ctx, connector_name)

    config = ReleaseConfig(
        token=token,
        url=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.git_repo_url.env_name, "git_repo_url"),
        owner=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.git_repo_owner.env_name,
                                           "git_repo_owner"),
        repo=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.git_repo_name.env_name, "git_repo_name"),
        default_branch=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.default_branch.env_name,
                                                    "default_branch"),
        release_branch=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.release_branch.env_name,
                                                    "release_branch"),
        git_print_stdout=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.print_git_stdout.env_name,
                                                      "print_git_stdout"),
        git_print_stderr=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.print_git_stderr.env_name,
                                                      "print_git_stderr"),
        release_commit_message=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                            runner_config.release_commit_message.env_name,
                                                            "release_commit_message"),
        release_version_prefix=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                            runner_config.release_version_prefix.env_name,
                                                            "release_version_prefix"),
        changelog_file=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                    runner_config.version_changelog_file.env_name,
                                                    "version_changelog_file"),
        version_file=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.version_file.env_name,
                                                  "version_file"),
        version_config_file=_resolve_env_and_cli_options(ctx, config_from_envs, runner_config.git_repo_name.env_name,
                                                         "git_repo_name"),
        version_config_text_append_missing=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                                        runner_config.version_config_append_missing.env_name,
                                                                        "version_config_append_missing"),
        version_config_marker=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                           runner_config.version_config_marker.env_name,
                                                           "version_config_marker"),
        version_config_marker_block_start=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                                       runner_config.version_config_marker_block_start.env_name,
                                                                       "version_config_marker_block_start"),
        version_config_marker_block_end=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                                     runner_config.version_config_marker_block_end.env_name,
                                                                     "version_config_marker_block_end"),
        auto_delete_temp_dir=_resolve_env_and_cli_options(ctx, config_from_envs,
                                                          runner_config.auto_delete_temp_dir.env_name,
                                                          "auto_delete_temp_dir")
    )
    log.info("Program finished successfully...")
