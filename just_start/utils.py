from functools import wraps
from platform import system
from subprocess import run, PIPE, STDOUT
from typing import Callable, List, Optional

from pexpect import spawn, EOF

from .client_handler import client_handler
from .config_reader import config
from .constants import SYNC_MSG


PASSWORD = config['general']['password']
BLOCKING_IP = config['general']['blocking_ip']

APP_SPECIFIC_COMMENT = '# just-start'
# noinspection SpellCheckingInspection
BLOCKING_LINES = '\\n'.join(
    [f'{BLOCKING_IP}\\t{blocked_site}\\t{APP_SPECIFIC_COMMENT}\\n'
     f'{BLOCKING_IP}\\twww.{blocked_site}\\t{APP_SPECIFIC_COMMENT}'
     for blocked_site in config['general']['blocked_sites']])
BLOCK_COMMAND = (f'/bin/bash -c "echo -e \'{BLOCKING_LINES}\' | '
                 f'sudo tee -a /etc/hosts > /dev/null"')
UNBLOCK_COMMAND = (f"sudo sed -i '' '/^.*{APP_SPECIFIC_COMMENT}$"
                   f"/d' /etc/hosts")


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ActionError(JustStartError):
    pass


class UserInputError(JustStartError, ValueError):
    pass


class PromptKeyboardInterrupt(JustStartError, KeyboardInterrupt):
    pass


def refresh_tasks(function_: Callable=None) -> Optional[Callable]:
    if function_:
        @wraps(function_)
        def decorator(*args, **kwargs) -> None:
            function_(*args, **kwargs)
            client_handler.on_tasks_refresh(get_task_list())

        return decorator

    client_handler.on_tasks_refresh(get_task_list())


def get_task_list() -> List[str]:
    return run_task().split("\n")


class GuiHandler:
    def __init__(self) -> None:
        self._pomodoro_status = ''
        self._status = ''

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, status) -> None:
        client_handler.write_status(status)
        self._status = status

    @property
    def pomodoro_status(self) -> str:
        return self._pomodoro_status

    @pomodoro_status.setter
    def pomodoro_status(self, pomodoro_status) -> None:
        client_handler.write_pomodoro_status(pomodoro_status)
        self._pomodoro_status = pomodoro_status

    @refresh_tasks
    def sync(self) -> None:
        self.status = SYNC_MSG
        self.status = run_task('sync')


gui_handler = GuiHandler()


def manage_blocked_sites(blocked: bool) -> None:
    if blocked:
        run_sudo(UNBLOCK_COMMAND, PASSWORD)
        run_sudo(BLOCK_COMMAND, PASSWORD)
    else:
        run_sudo(UNBLOCK_COMMAND, PASSWORD)


def manage_wifi(timer_running: bool=False) -> None:
    if timer_running:
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
