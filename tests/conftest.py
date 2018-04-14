from pytest import fixture
from unittest.mock import patch


@fixture(scope='session', autouse=True)
def mock_wifi_management():
    patch('just_start._just_start.manage_wifi')
