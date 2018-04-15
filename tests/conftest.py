from unittest.mock import patch, MagicMock

from pytest import fixture

from just_start import client


@fixture(scope='session', autouse=True)
def mock_subprocess_run():
    class RunMock(MagicMock):
        returncode = 0

    with patch('just_start.utils.run', lambda *_, **__: RunMock()), \
            patch('just_start.pomodoro.run', lambda *_, **__: RunMock()):
        yield


@fixture
def client_refresh():
    @client
    def on_tasks_refresh(_):
        pass


@fixture
def client_status():
    @client
    def write_status(_):
        pass


@fixture
def client_pomodoro():
    @client
    def write_pomodoro_status(_):
        pass
