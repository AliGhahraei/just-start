import shelve
from enum import Enum
from functools import wraps, partial
from pickle import HIGHEST_PROTOCOL
from platform import system
from signal import signal, SIGTERM
from subprocess import run, PIPE, STDOUT
from sys import exit
from typing import List, Optional, Dict, Callable, Any, Union

from pexpect import spawn, EOF

from .client_decorators import CLIENT_DECORATORS
from .config_reader import config
from .constants import (
    SYNC_MSG, PHASE_SKIP_PROMPT, HELP_MESSAGE, RECURRENCE_OFF, CONFIRMATION_OFF,
    PERSISTENT_PATH)
from just_start.pomodoro import PomodoroTimer, PomodoroError


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


def client(user_function: Union[Callable, str]):
    local_function_name = None

    def decorator(user_function_: Callable) -> Callable:
        if local_function_name not in CLIENT_DECORATORS:
            raise ValueError(f'{local_function_name} is not a valid client'
                             f' function')
        _client[local_function_name] = user_function_
        return user_function_

    if callable(user_function):
        local_function_name = user_function.__name__
        return decorator(user_function)

    local_function_name = user_function
    return decorator


def refresh(function_: Callable=None) -> Union[None, Callable]:
    if function_:
        @wraps(function_)
        def decorator(*args, **kwargs) -> None:
            function_(*args, **kwargs)
            _client.on_tasks_refresh(task_list_())

        return decorator

    _client.on_tasks_refresh(task_list_())


def task_list_() -> List[str]:
    return run_task().split("\n")


def write_on_error(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            func(*args, **kwargs)
        except TaskWarriorError as e:
            _client.write_status(str(e), error=True)

    return wrapper


class GuiHandler:
    def __init__(self) -> None:
        self._pomodoro_status = ''
        self._status = ''

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, status) -> None:
        _client.write_status(status)
        self._status = status

    @property
    def pomodoro_status(self) -> str:
        return self._pomodoro_status

    @pomodoro_status.setter
    def pomodoro_status(self, pomodoro_status) -> None:
        _client.write_pomodoro_status(pomodoro_status)
        self._pomodoro_status = pomodoro_status

    @refresh
    def sync(self) -> None:
        self.status = SYNC_MSG
        self.status = run_task('sync')


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


def get_timer_kwargs() -> Dict:
    try:
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
            timer_kwargs = {arg: db[arg] for arg
                            in PomodoroTimer.SERIALIZABLE_ATTRIBUTES}
    except KeyError:
        timer_kwargs = {}
    return timer_kwargs


network_handler = NetworkHandler()
gui_handler = GuiHandler()
_client = ClientHandler()
pomodoro_timer = PomodoroTimer(
    lambda status: gui_handler.__setattr__('pomodoro_status', status),
    network_handler.manage_blocked_sites, **get_timer_kwargs()
)


def init() -> None:
    signal(SIGTERM, _signal_handler)
    refresh()
    sync()


@write_on_error
def sync() -> None:
    gui_handler.sync()


def _signal_handler() -> None:
    quit_gracefully()


def quit_gracefully() -> None:
    sync()
    network_handler.manage_wifi()

    with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
        db.update(pomodoro_timer.serializable_data)
    exit()


def prompt_action_char() -> None:
    try:
        action_key = _client.prompt_char(
            'Waiting for user. Pressing h shows'
            ' available actions')
    except KeyboardInterrupt:
        raise ActionError(f'Ctrl+C was pressed with no action selected. Use'
                          f' q to quit')

    try:
        action = KEY_ACTIONS[action_key]
    except KeyError:
        raise ActionError(f'Unknown action key: "{action_key}"')

    execute_action(action)


def execute_action(action: 'Action') -> None:
    gui_handler.status = ''

    if action not in Action:
        raise ActionError(f'Unknown action: "{action}"')

    try:
        action()
    except (JustStartError, PomodoroError) as exc:
        _client.write_status(str(exc), error=True)
    except KeyboardInterrupt:
        # Cancel current action while it's still running
        pass


def input_task_ids() -> str:
    ids = _client.prompt_string("Enter the task's ids")

    while True:
        split_ids = ids.split(',')
        try:
            list(map(int, split_ids))
        except ValueError:
            ids = _client.prompt_string("Please enter valid ids", error=True)
        else:
            return ids


def skip_phases() -> None:
    prompt = PHASE_SKIP_PROMPT
    valid_phases = False

    while not valid_phases:
        try:
            phases = int(_client.prompt_string(prompt))
        except ValueError:
            pass
        else:
            if phases >= 1:
                pomodoro_timer.advance_phases(phases_skipped=phases)
                valid_phases = True
                network_handler.manage_wifi(timer_running=True)

        prompt = 'Please enter a valid number of phases'


def toggle_timer() -> None:
    pomodoro_timer.toggle()
    network_handler.manage_wifi(pomodoro_timer.is_running)


def reset_timer(at_work_user_overridden: Optional[bool]=None) -> None:
    pomodoro_timer.reset(at_work_user_overridden=at_work_user_overridden)
    network_handler.manage_wifi(timer_running=False)


def location_change() -> None:
    location = _client.prompt_string("Enter 'w' for work or anything else for"
                                     " home")
    at_work = location == 'w'
    reset_timer(at_work)
    toggle_timer()


@refresh
def add() -> None:
    name = _client.prompt_string("Enter the new task's data")
    gui_handler.status = run_task('add', *name.split())


@refresh
def delete() -> None:
    ids = input_task_ids()
    gui_handler.status = run_task(CONFIRMATION_OFF, RECURRENCE_OFF, ids,
                                  'delete')


@refresh
def modify() -> None:
    ids = input_task_ids()
    name = _client.prompt_string("Enter the modified task's data")
    gui_handler.status = run_task(RECURRENCE_OFF, ids, 'modify',
                                  *name.split())


@refresh
def complete() -> None:
    ids = input_task_ids()
    gui_handler.status = run_task(ids, 'done')


@refresh
def custom_command() -> None:
    command = _client.prompt_string('Enter your command')
    gui_handler.status = run_task(*command.split())


def show_help() -> None:
    gui_handler.status = HELP_MESSAGE


class Action(Enum):
    ADD = partial(add)
    COMPLETE = partial(complete)
    DELETE = partial(delete)
    SHOW_HELP = partial(show_help)
    SKIP_PHASES = partial(skip_phases)
    LOCATION_CHANGE = partial(location_change)
    MODIFY = partial(modify)
    TOGGLE_TIMER = partial(toggle_timer)
    QUIT_GRACEFULLY = partial(quit_gracefully)
    REFRESH = partial(refresh)
    RESET_TIMER = partial(reset_timer)
    SYNC = partial(sync)
    CUSTOM_COMMAND = partial(custom_command)

    def __call__(self, *args, **kwargs) -> None:
        self.value(*args, **kwargs)


KEY_ACTIONS = dict(zip(
    ('a', 'c', 'd', 'h', 'k', 'l', 'm', 'p', 'q', 'r', 's', 'y', '!'),
    Action.__members__.values()
))


def run_sudo(command: str, password: str) -> None:
    if password:
        child = spawn(command)

        try:
            child.sendline(password)
            child.expect(EOF)
        except OSError:
            pass


def run_task(*args) -> str:
    args = args or ['-BLOCKED']
    completed_process = run(['task', *args], stdout=PIPE, stderr=STDOUT)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output
