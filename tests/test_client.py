from just_start import client


# noinspection PyUnusedLocal
def test_client_decorator_definition_and_calls(mocker, no_wifi_handling):
    @client
    def write_status(_):
        pass

    @client
    def write_pomodoro_status(_):
        pass

    @client
    def on_tasks_refresh(_):
        pass
