from subprocess import CompletedProcess

from just_start.os_utils import run_task, TaskWarriorError, run_with_password
from pytest import raises


def test_run_task_raises_task_warrior_error(mocker):
    process = CompletedProcess([], stdout=b'', returncode=1)
    with raises(TaskWarriorError), \
            mocker.patch('just_start.os_utils.run_command', return_value=process) as run_command:
        run_task()
        run_command.assert_called_once()


def test_run_sudo_handles_os_error(mocker, caplog):
    test_command = 'test_command'
    with mocker.patch('just_start.os_utils._spawn_sudo_command', side_effect=OSError()):
        run_with_password(test_command, 'password')
    assert test_command in caplog.text
