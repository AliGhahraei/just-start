from just_start import client, ClientError
from just_start.client import refresh_tasks, StatusManager
from pytest import raises


def test_right_client_decoration(client_refresh, client_status,
                                 client_pomodoro):
    pass


def test_right_client_decoration_with_name_param():
    @client('write_status')
    def func():
        pass


def test_right_refresh_tasks(client_refresh):
    refresh_tasks()


def test_right_refresh_tasks_decoration(client_refresh):
    @refresh_tasks
    def refreshing_function():
        pass

    refreshing_function()


def test_right_status_manager(client_status, client_pomodoro):
    status_manager = StatusManager()

    assert hasattr(status_manager, 'app_status')
    assert hasattr(status_manager, 'pomodoro_status')

    status_manager.app_status = 'test'
    status_manager.pomodoro_status = 'test'
    status_manager.sync()


def test_wrong_client_decoration():
    with raises(ClientError):
        @client
        def wrong_name():
            pass
