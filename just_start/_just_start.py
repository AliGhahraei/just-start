from datetime import time, datetime
from functools import partial, wraps
from logging import getLogger, FileHandler, Formatter
from os import makedirs
from platform import system
from signal import signal, SIGTERM
from subprocess import run, PIPE, STDOUT
from sys import exit
from time import sleep
from traceback import format_exc
from typing import List, Optional, Dict, Callable, Any, Union

from pexpect import spawn, EOF
from toml import load

from .constants import (
    SYNC_MSG, PHASE_SKIP_PROMPT, HELP_MESSAGE, CONFIG_PATH, LOCAL_DIR,
    LOG_PATH, CONFIRMATION_OFF)
from just_start.pomodoro import PomodoroTimer, PomodoroError


logger = getLogger('just_start')
try:
    file_handler = FileHandler(LOG_PATH)
except FileNotFoundError:
    makedirs(LOCAL_DIR)
    file_handler = FileHandler(LOG_PATH)

logger.addHandler(file_handler)
file_handler.setFormatter(Formatter('%(asctime)s\n%(message)s'))


def validate_type(object_: Any, type_: type) -> Any:
    if not isinstance(object_, type_):
        raise TypeError(f'Not a {type_.__name__}')
    return object_


def validate_positive_int(int_: Any) -> int:
    if validate_type(int_, int) < 1:
        raise ValueError(f'Non-positive integer: "{int_}"')
    return int_


def validate_list(list_: Any) -> list:
    return validate_type(list_, list)


def validate_bool(bool_: Any) -> bool:
    return validate_type(bool_, bool)


def validate_time(time_str: Any) -> time:
    return as_time(validate_str(time_str))


def validate_str(str_: Any) -> str:
    return validate_type(str_, str)


def as_time(time_str: str) -> time:
    return datetime.strptime(time_str, '%H:%M').time()


VALID_CONFIG = {
    'general': {
        'password': ('', validate_str),
        'blocked_sites': ([], validate_list),
        'blocking_ip': ('127.0.0.1', validate_str),
    },
    'work': {
        'start': (as_time('09:00'), validate_time),
        'end': (as_time('18:00'), validate_time),
        'pomodoro_length': (25, validate_positive_int),
        'short_rest': (5, validate_positive_int),
        'long_rest': (15, validate_positive_int),
        'cycles_before_long_rest': (4, validate_positive_int),
    },
    'home': {
        'pomodoro_length': (25, validate_positive_int),
        'short_rest': (5, validate_positive_int),
        'long_rest': (15, validate_positive_int),
        'cycles_before_long_rest': (4, validate_positive_int),
    },
}


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ActionError(JustStartError):
    pass


def main() -> None:
    try:
        config = load(CONFIG_PATH)
    except FileNotFoundError:
        logger.warning(format_exc())
        config = {}

    value_errors = []
    for section_name, section_content in VALID_CONFIG.items():
        try:
            validate_config_section(config, section_name, section_content)
        except ValueError as e:
            value_errors.append(f'{e} (in {section_name})')
    if value_errors:
        value_errors = '\n'.join([error for error in value_errors])
        exit(f'Wrong configuration file:\n{value_errors}')

    network_handler = NetworkHandler(config)
    gui_handler = GuiHandler()
    gui_handler.draw_gui_and_statuses()
    signal(SIGTERM, partial(_signal_handler, gui_handler, network_handler))
    gui_handler.sync_or_write_error()

    action_loop(gui_handler, network_handler, config)


def write_on_error(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            func(*args, **kwargs)
        except TaskWarriorError as e:
            write_error(str(e))

    return wrapper


def draw_gui() -> None: pass


def write_status(status: str) -> None: print(status)


def write_error(error_msg: str) -> None: print(error_msg)


def write_pomodoro_status(status: str) -> None: print(status)


# noinspection PyUnusedLocal
def refresh_tasks(task_list) -> None: pass


def prompt_char(prompt: str) -> str: return input(prompt)


def prompt_string(prompt: str) -> str: return input(prompt)


def prompt_string_error(prompt: str) -> str: return input(prompt)


CLIENT_FUNCTIONS = {function_.__name__ for function_ in (
    draw_gui, write_status, write_error, write_pomodoro_status, refresh_tasks,
    prompt_char, prompt_string, prompt_string_error
)}


def client(user_function: Union[Callable, str]):
    function_name = None

    def decorator(user_function_: Callable) -> Callable:
        if function_name not in CLIENT_FUNCTIONS:
            raise ValueError(
                f'{function_name} is not a valid client function')

        globals()[function_name] = user_function_
        return user_function_

    if callable(user_function):
        function_name = user_function.__name__
        return decorator(user_function)
    else:
        function_name = user_function
        return decorator


def task_list_() -> List[str]:
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
        write_status(status)
        self._status = status

    @property
    def pomodoro_status(self) -> str:
        return self._pomodoro_status

    @pomodoro_status.setter
    def pomodoro_status(self, pomodoro_status) -> None:
        write_pomodoro_status(pomodoro_status)
        self._pomodoro_status = pomodoro_status

    def draw_gui_and_statuses(self) -> None:
        draw_gui()
        refresh_tasks(task_list_())
        write_pomodoro_status(self.pomodoro_status)

    @write_on_error
    def sync_or_write_error(self) -> None:
        self.sync()

    def sync(self) -> None:
        self.status = SYNC_MSG
        self.status = run_task('sync')


def input_task_ids() -> str:
    ids = prompt_string("Enter the task's ids")

    while True:
        split_ids = ids.split(',')
        try:
            list(map(int, split_ids))
        except ValueError:
            ids = prompt_string_error("Please enter valid ids")
        else:
            return ids


class NetworkHandler:
    def __init__(self, config: Dict) -> None:
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


def validate_config_section(config: Dict, section_name: str,
                            section_content: Dict) -> None:
    try:
        config[section_name]
    except KeyError:
        config[section_name] = section_content
    else:
        for field_name, field_content in section_content.items():
            default, validator = field_content
            try:
                config[section_name][field_name] = validator(
                    config[section_name][field_name])
            except KeyError:
                config[section_name][field_name] = default


def _signal_handler(gui_handler: GuiHandler,
                    network_handler: NetworkHandler, *_) -> None:
    _quit_gracefully(gui_handler, network_handler)


def _quit_gracefully(gui_handler: GuiHandler,
                     network_handler: NetworkHandler) -> None:
    gui_handler.sync_or_write_error()
    network_handler.manage_wifi()
    exit()


def action_loop(gui_handler: 'GuiHandler',
                network_handler: 'NetworkHandler', config: Dict):
    def add() -> None:
        name = prompt_string("Enter the new task's data")
        gui_handler.status = run_task('add', *name.split())

    def delete() -> None:
        ids = input_task_ids()
        gui_handler.status = run_task(CONFIRMATION_OFF, ids, 'delete')

    def modify() -> None:
        ids = input_task_ids()
        name = prompt_string("Enter the modified task's data")
        gui_handler.status = run_task(CONFIRMATION_OFF, ids, 'modify',
                                      *name.split())

    def complete() -> None:
        ids = input_task_ids()
        gui_handler.status = run_task(ids, 'done')

    def custom_command() -> None:
        command = prompt_string('Enter your command')
        gui_handler.status = run_task(*command.split())

    refreshing_actions = {
        'a': add,
        'c': complete,
        'd': delete,
        'm': modify,
        'y': gui_handler.sync,
        '!': custom_command,
    }

    def pomodoro_status(status: str):
        gui_handler.pomodoro_status = status

    with PomodoroTimer(pomodoro_status, network_handler.manage_blocked_sites,
                       config) as pomodoro_timer:
        def update_status(message: str):
            gui_handler.status = message

        non_refreshing_actions = {
            "KEY_RESIZE": partial(gui_handler.draw_gui_and_statuses),
            'h': partial(update_status, HELP_MESSAGE),
            'k': partial(skip_phases, network_handler, pomodoro_timer),
            'l': partial(location_change, network_handler, pomodoro_timer),
            'p': partial(toggle_timer, network_handler, pomodoro_timer),
            'q': partial(_quit_gracefully, gui_handler, network_handler),
            'r': partial(refresh_tasks, task_list_()),
            's': partial(reset_timer, network_handler, pomodoro_timer),
        }

        while True:
            try:
                execute_user_action(gui_handler, refreshing_actions,
                                    non_refreshing_actions)
            except (JustStartError, PomodoroError) as exc:
                write_error(str(exc))


def skip_phases(network_handler: 'NetworkHandler',
                timer: PomodoroTimer) -> None:
    prompt = PHASE_SKIP_PROMPT
    valid_phases = False

    while not valid_phases:
        try:
            phases = int(prompt_string(prompt))
        except ValueError:
            pass
        else:
            if phases >= 1:
                timer.advance_phases(phases_skipped=phases)
                valid_phases = True
                network_handler.manage_wifi(timer_running=True)

        prompt = 'Please enter a valid number of phases'


def toggle_timer(network_handler: 'NetworkHandler',
                 timer: PomodoroTimer) -> None:
    timer.toggle()
    network_handler.manage_wifi(timer.is_running)


def reset_timer(network_handler: 'NetworkHandler', timer: PomodoroTimer,
                at_work_user_overridden: Optional[bool]=None) -> None:
    timer.reset(at_work_user_overridden=at_work_user_overridden)
    network_handler.manage_wifi(timer_running=False)


def location_change(network_handler: 'NetworkHandler',
                    timer: PomodoroTimer) -> None:
    location = prompt_string("Enter 'w' for work or anything else for home")
    at_work = location == 'w'
    reset_timer(network_handler, timer, at_work)
    toggle_timer(network_handler, timer)


FunctionDict = Dict[str, Callable[[], None]]


def execute_user_action(gui_handler: GuiHandler,
                        refreshing_actions: FunctionDict,
                        non_refreshing_actions: FunctionDict) -> None:
    try:
        read_char = prompt_char('Waiting for user. Pressing h shows available'
                                ' actions')
        gui_handler.status = ''
        sleep(0.1)
    except KeyboardInterrupt:
        raise ActionError(f'No action was selected yet, but Ctrl+C was pressed'
                          f'. Use q to quit')

    try:
        refreshing_actions[read_char]()
    except KeyError:
        try:
            non_refreshing_actions[read_char]()
        except KeyError:
            raise ActionError(f'Unknown key action: "{read_char}"')
        except KeyboardInterrupt:
            # Cancel current action
            pass
    except KeyboardInterrupt:
        # Cancel current action
        pass
    else:
        refresh_tasks(task_list_())


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
