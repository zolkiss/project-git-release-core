from project_git_release.classes import NewVersion


def test_new_version_get_full_version():
    new_version = NewVersion("0.0.1", "")
    assert "0.0.1" == new_version.get_full_version()


def test_new_version_get_full_version_with_prefix():
    new_version = NewVersion("0.0.1", "v")
    assert "v0.0.1" == new_version.get_full_version()
