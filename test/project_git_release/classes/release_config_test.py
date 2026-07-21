def test_release_config_no_verbose_flag(release_config):
    assert "--no-verbose" == release_config.git_verbose_flag()


def test_release_config_verbose_flag(release_config):
    release_config.git_verbose_logging = True
    assert "--verbose" == release_config.git_verbose_flag()
