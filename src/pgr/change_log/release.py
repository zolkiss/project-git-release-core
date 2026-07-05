import datetime

from pgr.change_log import generate_change_chapters
from pgr.conv_commit.resolver import GroupedConvCommits
from pgr.interfaces import GitRelease


def generate_release_log(grouped_commits: GroupedConvCommits, previous_version: GitRelease | None,
                         new_version: GitRelease) -> str:
    compare_text = f"{new_version.tag_name}"
    if previous_version is not None:
        compare_text = f"{previous_version.tag_name}...{new_version.tag_name}"

    new_changes = f"## [{new_version.tag_name}](https://gitea.raspi.zolkiss.home/KiZoCo/testing-repository-with-releases/compare/{compare_text}) ({datetime.datetime.now().strftime("%Y-%m-%d")})\n"
    if grouped_commits.has_breaking_change():
        new_changes += "\n".join(generate_change_chapters("Breaking changes",
                                                          [grouped_commits.braking_changes]))
    if grouped_commits.has_feature():
        new_changes += "\n".join(generate_change_chapters("Features",
                                                          [grouped_commits.get_features()]))
    if grouped_commits.has_fix():
        new_changes += "\n".join(generate_change_chapters("Bugfix(es)",
                                                          [grouped_commits.get_fixes()]))
    if grouped_commits.has_other_change():
        new_changes += "\n".join(generate_change_chapters("Other changes",
                                                          [grouped_commits.get_other_changes(),
                                                           grouped_commits.invalid_commits], True))
    new_changes += "---\n"
    return new_changes
