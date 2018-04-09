from functools import wraps
from platform import system
from subprocess import run, PIPE, STDOUT
from typing import Callable, List, Optional

from pexpect import spawn, EOF

from .client import client
from .config_reader import CONFIG
from .constants import SYNC_MSG


PASSWORD = CONFIG['general']['password']
BLOCKING_IP = CONFIG['general']['blocking_ip']

APP_SPECIFIC_COMMENT = '# just-start'
# noinspection SpellCheckingInspection
BLOCKING_LINES = '\\n'.join(
    [f'{BLOCKING_IP}\\t{blocked_site}\\t{APP_SPECIFIC_COMMENT}\\n'
     f'{BLOCKING_IP}\\twww.{blocked_site}\\t{APP_SPECIFIC_COMMENT}'
     for blocked_site in CONFIG['general']['blocked_sites']])
BLOCK_COMMAND = (f'/bin/bash -c "echo -e \'{BLOCKING_LINES}\' | sudo tee -a' 
                 f' /etc/hosts > /dev/null"')
UNBLOCK_COMMAND = f"sudo sed -i '' '/^.*{APP_SPECIFIC_COMMENT}$/d' /etc/hosts"


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ActionError(JustStartError):
    pass


class UserInputError(JustStartError, ValueError):
    pass


def refresh_tasks(f: Callable=None) -> Optional[Callable]:
    """Refresh tasks or decorate a function to call refresh after its code.

    :param f: call to execute before refreshing
    :return: a decorated refreshing function if used as decorator
    :raise TaskWarriorError if sync fails
    """

    if f:
        @wraps(f)
        def decorator(*args, **kwargs) -> None:
            f(*args, **kwargs)
            client.on_tasks_refresh(get_task_list())

        return decorator

    client.on_tasks_refresh(get_task_list())


def get_task_list() -> List[str]:
    return run_task().split("\n")


class StatusManager:
    def __init__(self) -> None:
        self._pomodoro_status = ''
        self._status = ''

    @property
    def app_status(self) -> str:
        return self._status

    @app_status.setter
    def app_status(self, status) -> None:
        client.write_status(status)
        self._status = status

    @property
    def pomodoro_status(self) -> str:
        return self._pomodoro_status

    @pomodoro_status.setter
    def pomodoro_status(self, pomodoro_status) -> None:
        client.write_pomodoro_status(pomodoro_status)
        self._pomodoro_status = pomodoro_status

    @refresh_tasks
    def sync(self) -> None:
        self.app_status = SYNC_MSG
        self.app_status = run_task('sync')


def block_sites(block: bool) -> None:
    # Always delete outdated blocked sites
    run_sudo(UNBLOCK_COMMAND, PASSWORD)

    if block:
        run_sudo(BLOCK_COMMAND, PASSWORD)


def manage_wifi(*, enable: bool=False) -> None:
    if enable:
        if system() == 'Linux':
            # noinspection SpellCheckingInspection
            run_sudo('sudo systemctl start netctl-auto@wlp2s0', PASSWORD)
        else:
            # noinspection SpellCheckingInspection
            run_sudo('networksetup -setairportpower en0 on', PASSWORD)
    else:
        if system() == 'Linux':
            # noinspection SpellCheckingInspection
            run_sudo('sudo systemctl stop netctl-auto@wlp2s0', PASSWORD)
        else:
            # noinspection SpellCheckingInspection
            run_sudo('networksetup -setairportpower en0 off', PASSWORD)


def run_task(*args) -> str:
    args = args or ['-BLOCKED']
    completed_process = run(['task', *args], stdout=PIPE, stderr=STDOUT)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output


def run_sudo(command: str, password: str) -> None:
    if password:
        child = spawn(command)

        try:
            child.sendline(password)
            child.expect(EOF)
        except OSError:
            pass
