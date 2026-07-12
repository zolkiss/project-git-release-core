import datetime

from project_git_release.classes import GitRelease
from project_git_release.classes.conv_commit import ConvCommitDetails, GroupedConvCommits
from project_git_release.core import ReleaseConfig


def generate_change_chapters(chapter_title: str, changes: list[list[ConvCommitDetails]],
                             include_type: bool = False) -> list[str]:
    change_chapter = [f"### {chapter_title}"]
    if len(changes) == 1:
        final_changes = changes[0]
    else:
        final_changes = []
        for change in changes:
            final_changes.extend(change)

    sorted_list = sorted(final_changes, key=lambda x: x.creation_datetime, reverse=True)

    change_chapter.extend(_generate_change_records(sorted_list, include_type))
    change_chapter.extend([""])
    return change_chapter


def _generate_change_records(changes: list[ConvCommitDetails], include_type: bool) -> list[
    str]:
    change_records = []
    for change in changes:
        if change.valid:
            if change.scope is not None and include_type:
                scope = f"**{change.type}({change.scope}):**"
            elif change.scope is not None:
                scope = f"**{change.scope}:**"
            else:
                if include_type:
                    scope = f"**{change.type}:**"
                else:
                    scope = ""
            change_records.append(f"* {scope} {change.description}")
        else:
            change_records.append(f"* {change.description}")
    return change_records


def generate_release_log(config: ReleaseConfig, grouped_commits: GroupedConvCommits,
                         previous_version: GitRelease | None,
                         new_version: GitRelease) -> str:
    compare_text = f"{new_version.tag_name}"
    if previous_version is not None:
        compare_text = f"{previous_version.tag_name}...{new_version.tag_name}"

    new_changes = f"## [{new_version.tag_name}]({config.git_url()}/compare/{compare_text}) ({datetime.datetime.now().strftime("%Y-%m-%d")})\n"
    if grouped_commits.has_breaking_change():
        new_changes += "\n".join(generate_change_chapters("Breaking changes",
                                                          [grouped_commits.braking_changes]))
    if grouped_commits.has_feature():
        new_changes += "\n".join(generate_change_chapters("Features",
                                                          [grouped_commits.get_features()]))
    if grouped_commits.has_fix():
        new_changes += "\n".join(generate_change_chapters("Bugfix(es)",
                                                          [grouped_commits.get_fixes()]))
    if (grouped_commits.has_other_change()
            or len(grouped_commits.invalid_commits) > 0):
        new_changes += "\n".join(generate_change_chapters("Other changes",
                                                          [grouped_commits.get_other_changes(),
                                                           grouped_commits.invalid_commits], True))
    new_changes += "---\n"
    return new_changes
