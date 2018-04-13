from just_start import client, Action


# noinspection PyUnusedLocal
def test_client_decorator_definition_and_calls(mocker, no_wifi_handling):
    @client
    def write_status(*_):
        functions_called[write_status] = True

    @client
    def write_pomodoro_status(*_):
        functions_called[write_pomodoro_status] = True

    @client
    def on_tasks_refresh(*_):
        functions_called[on_tasks_refresh] = True

    functions_called = {function_: False for function_ in
                        (write_status, write_pomodoro_status, on_tasks_refresh)}

    with mocker.patch('just_start._just_start.refresh_tasks'):
        Action.REFRESH_TASKS()

    with mocker.patch('just_start.pomodoro.run'):
        Action.STOP_TIMER()

    for function_, called in functions_called.items():
        assert called, f'{function_.__name__} was not called'
