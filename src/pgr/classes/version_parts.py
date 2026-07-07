from enum import StrEnum


class VersionParts(StrEnum):
    FULL_VERSION = "version"
    PREFIX = "prefix"
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE_RELEASE = "prerelease"
    BUILD_META_DATA = "buildmetadata"
