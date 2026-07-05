from pgr.conv_commit import ConvCommitDetails


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
                scope = ""
            change_records.append(f"* {scope} {change.description}")
        else:
            change_records.append(f"* {change.description}")
    return change_records
