import re
from enum import StrEnum


class VersionParts(StrEnum):
    FULL_VERSION = "version"
    PREFIX = "prefix"
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE_RELEASE = "prerelease"
    BUILD_META_DATA = "buildmetadata"


def build_version_regex(prefix: str = "") -> re.Pattern:
    escaped_prefix = re.escape(prefix)
    pattern = (
        rf"(?P<{VersionParts.FULL_VERSION}>"
        rf"(?P<{VersionParts.PREFIX}>{escaped_prefix})?"
        rf"(?P<{VersionParts.MAJOR}>0|[1-9]\d*)"
        r"\."
        rf"(?P<{VersionParts.MINOR}>0|[1-9]\d*)"
        r"\."
        rf"(?P<{VersionParts.PATCH}>0|[1-9]\d*)"
        rf"(?:-(?P<{VersionParts.PRE_RELEASE}>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        rf"(?:\+(?P<{VersionParts.BUILD_META_DATA}>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
        r")"
    )
    return re.compile(pattern)
