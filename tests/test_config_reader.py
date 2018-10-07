from just_start.config_reader import get_config, load_config, get_client_config


def test_config_works_with_defaults():
    assert get_config().general


def test_missing_config_file(mocker):
    with mocker.patch('just_start.config_reader.load', side_effect=FileNotFoundError()):
        assert load_config().general


def test_client_config():
    assert not get_client_config('unconfigured_client')
