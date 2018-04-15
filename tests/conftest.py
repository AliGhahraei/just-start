from unittest.mock import patch
from subprocess import CompletedProcess

from pytest import fixture

from just_start import client


@fixture(scope='session', autouse=True)
def mock_run():
    def run_mock(*args, **__):
        return CompletedProcess(args, stdout=b'', returncode=0)

    with patch('just_start.os_utils.run', run_mock), \
            patch('just_start.pomodoro.run', run_mock):
        yield


@fixture(scope='session', autouse=True)
def mock_spawn():
    with patch('just_start.os_utils.spawn'):
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
