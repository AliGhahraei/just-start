from functools import wraps
from platform import system
from subprocess import run, PIPE, STDOUT
from typing import Callable, List, Union

from pexpect import spawn, EOF

from .config_reader import config
from .constants import SYNC_MSG


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ActionError(JustStartError):
    pass


class ClientHandler(dict):
    def __init__(self) -> None:
        super().__init__()
        self._functions = {}

    def __setitem__(self, key: str, value: Callable):
        self._functions[key] = value

    def __getitem__(self, item: str):
        return self._functions[item]

    def __getattr__(self, item: str) -> Callable:
        return self[item]


client_handler = ClientHandler()


def refresh(function_: Callable=None) -> Union[None, Callable]:
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

    @refresh
    def sync(self) -> None:
        self.status = SYNC_MSG
        self.status = run_task('sync')


gui_handler = GuiHandler()


class NetworkHandler:
    def __init__(self) -> None:
        self.password = config['general']['password']
        blocked_sites = config['general']['blocked_sites']
        blocking_ip = config['general']['blocking_ip']

        app_specific_comment = '# just-start'
        # noinspection SpellCheckingInspection
        blocking_lines = '\\n'.join(
            [f'{blocking_ip}\\t{blocked_site}\\t{app_specific_comment}\\n'
             f'{blocking_ip}\\twww.{blocked_site}\\t{app_specific_comment}'
             for blocked_site in blocked_sites])

        self.block_command = (f'/bin/bash -c "echo -e \'{blocking_lines}\' | '
                              f'sudo tee -a /etc/hosts > /dev/null"')
        self.unblock_command = (f"sudo sed -i '' '/^.*{app_specific_comment}$"
                                f"/d' /etc/hosts")

    def manage_blocked_sites(self, blocked: bool) -> None:
        if blocked:
            run_sudo(self.unblock_command, self.password)
            run_sudo(self.block_command, self.password)
        else:
            run_sudo(self.unblock_command, self.password)

    def manage_wifi(self, timer_running: bool=False) -> None:
        if timer_running:
            if system() == 'Linux':
                # noinspection SpellCheckingInspection
                run_sudo('sudo systemctl start netctl-auto@wlp2s0',
                         self.password)
            else:
                # noinspection SpellCheckingInspection
                run_sudo('networksetup -setairportpower en0 on',
                         self.password)
        else:
            if system() == 'Linux':
                # noinspection SpellCheckingInspection
                run_sudo('sudo systemctl stop netctl-auto@wlp2s0',
                         self.password)
            else:
                # noinspection SpellCheckingInspection
                run_sudo('networksetup -setairportpower en0 off',
                         self.password)


network_handler = NetworkHandler()


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
