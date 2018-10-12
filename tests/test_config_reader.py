from just_start.config_reader import get_general_config, get_client_config


def test_get_config_without_file(mocker):
    with mocker.patch('just_start.config_reader.load', side_effect=FileNotFoundError()):
        assert get_general_config()


def test_client_config():
    assert not get_client_config('unconfigured_client')
