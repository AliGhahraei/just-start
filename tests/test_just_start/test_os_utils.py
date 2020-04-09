import shelve
from subprocess import CompletedProcess
from unittest.mock import patch

from just_start.config_reader import GeneralConfig
from just_start.os_utils import run_task, TaskWarriorError, run_sudo, Db
from pytest import raises, fixture


@fixture
def database(mocker):
    return Db(mocker.create_autospec(shelve.open))


class TestDb:
    def test_getitem(self, database):
        assert database['key']

    def test_setitem(self, database):
        database['key'] = 'value'

    def test_update(self, database):
        database.update({'key': 'value'})


def test_run_task_raises_error_after_command_failure(mocker):
    process = CompletedProcess([], stdout=b'', returncode=1)
    with raises(TaskWarriorError), \
            mocker.patch('just_start.os_utils.run_command', return_value=process) as run_command:
        run_task()
        run_command.assert_called_once()


def test_run_sudo():
    run_sudo('test_command', _get_config_with_password)


def test_run_sudo_handles_os_error(caplog):
    test_command = 'test_command'
    with patch('just_start.os_utils.spawn', side_effect=OSError()):
        run_sudo(test_command, _get_config_with_password)
    assert test_command in caplog.text


def _get_config_with_password():
    return GeneralConfig(password='password')
