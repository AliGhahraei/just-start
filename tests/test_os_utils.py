from subprocess import CompletedProcess

from just_start.config_reader import GeneralConfig
from just_start.os_utils import run_task, TaskWarriorError, run_sudo
from pytest import raises


def test_run_task_raises_error_after_command_failure(mocker):
    process = CompletedProcess([], stdout=b'', returncode=1)
    with raises(TaskWarriorError), \
            mocker.patch('just_start.os_utils.run_command', return_value=process) as run_command:
        run_task()
        run_command.assert_called_once()


def test_run_with_sudo_handles_os_error(mocker, caplog):
    test_command = 'test_command'
    with mocker.patch('just_start.os_utils.spawn', side_effect=OSError()):
        run_sudo(test_command, lambda: GeneralConfig(password='password'))
    assert test_command in caplog.text
