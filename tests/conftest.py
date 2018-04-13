from pytest import fixture
from unittest.mock import patch


@fixture
def no_wifi_handling():
    with patch('just_start._just_start.manage_wifi'):
        yield
