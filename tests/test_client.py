from just_start import client, ClientError
from just_start.client import refresh_tasks, StatusManager
from pytest import raises, mark, fixture


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


@mark.use_fixtures('client_refresh', 'client_status', 'client_pomodoro')
def test_right_client_decoration():
    pass


def test_right_client_decoration_with_name_param():
    @client('write_status')
    def func(_):
        pass


@mark.use_fixtures('client_refresh')
def test_right_refresh_tasks():
    refresh_tasks()


@mark.use_fixtures('client_refresh')
def test_right_refresh_tasks_decoration():
    @refresh_tasks
    def refreshing_function():
        pass

    refreshing_function()


@mark.use_fixtures('client_pomodoro', 'client_status')
def test_right_status_manager():
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
