from just_start import client, ClientError
from just_start.client import refresh_tasks
from pytest import raises


def test_right_client_decoration():
    @client
    def write_status(_):
        pass

    @client
    def write_pomodoro_status(_):
        pass

    @client
    def on_tasks_refresh(_):
        pass


def test_right_client_decoration_with_name_param():
    @client('write_status')
    def func():
        pass


def test_right_refresh_tasks_decoration():
    @client
    def on_tasks_refresh(_):
        pass

    @refresh_tasks
    def refreshing_function():
        pass

    refreshing_function()


def test_wrong_client_decoration():
    with raises(ClientError):
        @client
        def wrong_name():
            pass
