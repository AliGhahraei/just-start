from pytest import fixture
from unittest.mock import patch


@fixture(scope='session', autouse=True)
def mock_subprocess_run():
    patch('just_start.utils.run')
    patch('just_start.pomodoro.run')
