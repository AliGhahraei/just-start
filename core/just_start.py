from abc import ABC, abstractmethod
from functools import partial, wraps
from logging import error as log_error, basicConfig as loggingConfig
from os import makedirs
from platform import system
from signal import signal, SIGTERM
from subprocess import run, PIPE, STDOUT
from time import sleep
from typing import List, Optional, Dict, Callable, Any
from sys import exit

from pexpect import spawn, EOF
from yaml import safe_load

from core.constants import (
    SYNC_MSG, PHASE_SKIP_PROMPT, CONFIG_PATH, LOCAL_DIR, HELP_MESSAGE, LOG_PATH)
from pomodoro import PomodoroTimer, PomodoroError


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ConfigurationMissingError(JustStartError, FileNotFoundError):
    pass


class ActionError(JustStartError):
    pass


def start(gui_handler: 'GuiHandler', prompt_handler: 'PromptHandler') -> None:
    try:
        config = parse_config()
    except ConfigurationMissingError as e:
        print(str(e))
        exit(1)
    else:
        try:
            loggingConfig(filename=LOG_PATH, format='%(asctime)s %(message)s')
        except FileNotFoundError:
            makedirs(LOCAL_DIR)
            loggingConfig(filename=LOG_PATH, format='%(asctime)s %(message)s')

        network_handler = NetworkHandler(config)
        gui_handler.draw_gui()
        signal(SIGTERM, partial(_signal_handler, gui_handler, network_handler))
        gui_handler.sync_or_write_error()

        action_loop(gui_handler, prompt_handler, network_handler, config)


def parse_config() -> Dict:
    try:
        with open(CONFIG_PATH) as f:
            return safe_load(f)
    except FileNotFoundError:
        raise ConfigurationMissingError(
            f"No config file at '{CONFIG_PATH}'. Check if it's really there"
            f" (and its permissions) or create one if it's the first time you"
            f" use this app")


def write_on_error(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            func(*args, **kwargs)
        except TaskWarriorError as e:
            self = args[0]
            self.write_error(str(e))

    return wrapper


class GuiHandler(ABC):
    @property
    def task_list(self) -> List[str]:
        return run_task().split("\n")

    @abstractmethod
    def draw_gui(self) -> None: pass

    @abstractmethod
    def write_status(self, status: str) -> None: pass

    @abstractmethod
    def write_error(self, error_msg: str) -> None: pass

    @abstractmethod
    def write_pomodoro_status(self, status: str) -> None: pass

    @abstractmethod
    def refresh_tasks(self) -> None: pass

    @write_on_error
    def sync_or_write_error(self) -> None:
        self.sync()

    def sync(self) -> None:
        self.write_status(SYNC_MSG)
        self.write_status(run_task(['sync']))


class PromptHandler(ABC):
    @abstractmethod
    def prompt_char(self, status: str) -> str: pass

    @abstractmethod
    def prompt_string(self, status: str) -> str: pass

    @abstractmethod
    def prompt_string_error(self, error_msg: str) -> str: pass

    def input_taskids(self) -> str:
        ids = self.prompt_string("Enter the task's ids")

        while True:
            splitted_ids = ids.split(',')
            try:
                list(map(int, splitted_ids))
            except ValueError:
                ids = self.prompt_string_error("Please enter valid ids")
            else:
                return ids


class NetworkHandler:
    def __init__(self, config: Dict):
        self.password = config['password']

        blocking_lines = '\\n'.join(
            [f'127.0.0.1\\t{blocked_site}\\t#juststart\\n'
             f'127.0.0.1\\twww.{blocked_site}\\t#juststart'
             for blocked_site in config['blocked_sites']])

        self.block_command = (f'/bin/bash -c "echo -e \'{blocking_lines}\' | '
                              f'sudo tee -a /etc/hosts > /dev/null"')
        self.unblock_command = 'sudo sed -i -e /#juststart$/d /etc/hosts'

    def manage_blocked_sites(self, blocked: bool) -> None:
        if blocked:
            run_sudo(self.unblock_command, self.password)
            run_sudo(self.block_command, self.password)
        else:
            run_sudo(self.unblock_command, self.password)

    def manage_wifi(self, timer_running: bool=False) -> None:
        if timer_running:
            if system() == 'Linux':
                run_sudo('sudo systemctl start netctl-auto@wlp2s0',
                         self.password)
            else:
                run_sudo('networksetup -setairportpower en0 on',
                         self.password)
        else:
            if system() == 'Linux':
                run_sudo('sudo systemctl stop netctl-auto@wlp2s0',
                         self.password)
            else:
                run_sudo('networksetup -setairportpower en0 off',
                         self.password)


def _signal_handler(gui_handler: GuiHandler,
                    network_handler: NetworkHandler, *_) -> None:
    _quit_gracefully(gui_handler, network_handler)


def _quit_gracefully(gui_handler: GuiHandler,
                     network_handler: NetworkHandler) -> None:
    gui_handler.sync_or_write_error()
    network_handler.manage_wifi()
    exit()


def action_loop(gui_handler: 'GuiHandler',
                prompt_handler: PromptHandler,
                network_handler: 'NetworkHandler', config: Dict):
    def add() -> None:
        name = prompt_handler.prompt_string("Enter the new task's data")
        gui_handler.write_status(run_task(['add'] + name.split()))

    def delete() -> None:
        ids = prompt_handler.input_taskids()
        gui_handler.write_status(run_task([ids, 'delete',
                                           'rc.confirmation=off']))

    def modify() -> None:
        ids = prompt_handler.input_taskids()
        name = prompt_handler.prompt_string("Enter the modified task's data")
        gui_handler.write_status(run_task([ids, 'modify'] + name.split()))

    def complete() -> None:
        ids = prompt_handler.input_taskids()
        gui_handler.write_status(run_task([ids, 'done']))

    def custom_command() -> None:
        command = prompt_handler.prompt_string('Enter your command')
        gui_handler.write_status(run_task(command.split()))

    refreshing_actions = {
        'a': add,
        'c': complete,
        'd': delete,
        'm': modify,
        'y': gui_handler.sync,
        '!': custom_command,
    }

    with PomodoroTimer(gui_handler.write_pomodoro_status,
                       network_handler.manage_blocked_sites, config,
                       CONFIG_PATH) as pomodoro_timer:
        non_refreshing_actions = {
            "KEY_RESIZE": partial(gui_handler.draw_gui),
            'h': partial(gui_handler.write_status, HELP_MESSAGE),
            'k': partial(skip_phases, prompt_handler, network_handler,
                         pomodoro_timer),
            'l': partial(location_change, prompt_handler, network_handler,
                         pomodoro_timer),
            'p': partial(toggle_timer, network_handler, pomodoro_timer),
            'q': partial(_quit_gracefully, gui_handler, network_handler),
            'r': partial(gui_handler.refresh_tasks),
            's': partial(reset_timer, network_handler, pomodoro_timer),
        }

        while True:
            try:
                execute_user_action(prompt_handler, gui_handler,
                                    refreshing_actions, non_refreshing_actions)
            except (JustStartError, PomodoroError) as exc:
                gui_handler.write_error(str(exc))


def skip_phases(prompt_handler: PromptHandler,
                network_handler: 'NetworkHandler',
                timer: PomodoroTimer) -> None:
    prompt = PHASE_SKIP_PROMPT
    valid_phases = False

    while not valid_phases:
        try:
            phases = int(prompt_handler.prompt_string(prompt))
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


def location_change(prompt_handler: PromptHandler,
                    network_handler: 'NetworkHandler',
                    timer: PomodoroTimer) -> None:
    location = prompt_handler.prompt_string("Enter 'w' for work or anything"
                                            " else for home")
    at_work = location == 'w'
    reset_timer(network_handler, timer, at_work)
    toggle_timer(network_handler, timer)


FunctionDict = Dict[str, Callable[[], None]]


def execute_user_action(prompt_handler: PromptHandler,
                        gui_handler: GuiHandler,
                        refreshing_actions: FunctionDict,
                        non_refreshing_actions: FunctionDict) -> None:
    try:
        read_char = prompt_handler.prompt_char('Waiting for user.'
                                               ' Pressing h shows'
                                               ' available actions')
        gui_handler.write_status('')
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
        gui_handler.refresh_tasks()


def run_sudo(command: str, password: str) -> None:
    child = spawn(command)

    try:
        child.sendline(password)
        child.expect(EOF)
    except OSError:
        pass


def log_failure(error_: Exception, message: str='') -> None:
    print(message)
    log_error(f'{type(error_)}: {error_}')
    print(f'Log written to "{LOG_PATH}"')
    exit(1)


def run_task(arg_list: Optional[List[str]]=None) -> str:
    arg_list = arg_list or []
    completed_process = run(['task'] + arg_list, stdout=PIPE, stderr=STDOUT)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output
