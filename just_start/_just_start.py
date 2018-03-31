import shelve
from enum import Enum
from functools import wraps, partial
from pickle import HIGHEST_PROTOCOL
from signal import signal, SIGTERM
from sys import exit
from typing import Dict, Callable, Union

from .client_decorators import CLIENT_DECORATORS
from .utils import (
    client_handler, gui_handler, refresh_tasks, run_task, manage_blocked_sites,
    manage_wifi, JustStartError, UserInputError,
    PromptKeyboardInterrupt)

from .constants import (
    PHASE_SKIP_PROMPT, HELP_MESSAGE, RECURRENCE_OFF, CONFIRMATION_OFF,
    PERSISTENT_PATH)
from just_start.pomodoro import PomodoroTimer


pomodoro_timer = PomodoroTimer(
    lambda status: gui_handler.__setattr__('pomodoro_status', status),
    manage_blocked_sites
)


def client(user_function: Union[Callable, str]):
    local_function_name = None

    def decorator(user_function_: Callable) -> Callable:
        if local_function_name not in CLIENT_DECORATORS:
            raise ValueError(f'{local_function_name} is not a valid client'
                             f' function')
        client_handler[local_function_name] = user_function_
        return user_function_

    if callable(user_function):
        local_function_name = user_function.__name__
        return decorator(user_function)

    local_function_name = user_function
    return decorator


def write_errors_option(func):
    @wraps(func)
    def wrapper(*args, write_errors=True, **kwargs):
        if write_errors:
            try:
                func(*args, **kwargs)
            except JustStartError as e:
                client_handler.write_status(str(e), error=True)
        else:
            func(*args, **kwargs)
    return wrapper


# noinspection PyUnusedLocal
@write_errors_option
def init(write_errors: bool=True) -> None:
    read_serialized_data()
    handle_sigterm()
    refresh_tasks_and_sync()


def read_serialized_data() -> Dict:
    try:
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
            data = {arg: db[arg] for arg
                    in PomodoroTimer.SERIALIZABLE_ATTRIBUTES}
    except KeyError:
        data = {}

    pomodoro_timer.serializable_data = data
    return data


def handle_sigterm():
    signal(SIGTERM, _signal_handler)


def refresh_tasks_and_sync():
    refresh_tasks()
    sync()


def sync() -> None:
    gui_handler.sync()


# noinspection PyUnusedLocal
@write_errors_option
def prompt_and_exec_action(write_errors=True) -> None:
    try:
        action_key = client_handler.prompt_char(
            'Waiting for user. Pressing h shows'
            ' available actions')
    except KeyboardInterrupt:
        raise PromptKeyboardInterrupt(f'Ctrl+C was pressed with no action'
                                      f' selected. Use q to quit')
    else:
        try:
            action = KEY_ACTIONS[action_key]
        except KeyError:
            raise UserInputError(f'Unknown action key: "{action_key}"')
        else:
            try:
                action()
            except KeyboardInterrupt:
                # Cancel current action while it's still running
                pass


def _signal_handler() -> None:
    quit_gracefully()


def quit_gracefully() -> None:
    sync()
    manage_wifi()
    serialize_timer()
    exit()


def serialize_timer() -> None:
    with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
        db.update(pomodoro_timer.serializable_data)


def input_task_ids() -> str:
    ids = client_handler.prompt_string("Enter the task's ids")

    split_ids = ids.split(',')
    try:
        list(map(int, split_ids))
    except ValueError:
        raise UserInputError(f'Invalid id list "{ids}"')

    return ids


def skip_phases() -> None:
    prompt = PHASE_SKIP_PROMPT
    valid_phases = False

    while not valid_phases:
        try:
            phases = int(client_handler.prompt_string(prompt))
        except ValueError:
            pass
        else:
            if phases >= 1:
                pomodoro_timer.advance_phases(phases_skipped=phases)
                valid_phases = True
                manage_wifi(timer_running=True)

        prompt = 'Please enter a valid number of phases'


def toggle_timer() -> None:
    pomodoro_timer.toggle()
    manage_wifi(pomodoro_timer.is_running)


def reset_timer(at_work_user_overridden: bool=False) -> None:
    pomodoro_timer.reset(at_work=at_work_user_overridden)
    manage_wifi(timer_running=False)


def location_change() -> None:
    location = client_handler.prompt_string("Enter 'w' for work or anything"
                                            " else for home")
    at_work = location == 'w'
    reset_timer(at_work)
    toggle_timer()


@refresh_tasks
def add() -> None:
    name = client_handler.prompt_string("Enter the new task's data")
    gui_handler.status = run_task('add', *name.split())


@refresh_tasks
def delete() -> None:
    ids = input_task_ids()
    gui_handler.status = run_task(CONFIRMATION_OFF, RECURRENCE_OFF, ids,
                                  'delete')


@refresh_tasks
def modify() -> None:
    ids = input_task_ids()
    name = client_handler.prompt_string("Enter the modified task's data")
    gui_handler.status = run_task(RECURRENCE_OFF, ids, 'modify',
                                  *name.split())


@refresh_tasks
def complete() -> None:
    ids = input_task_ids()
    gui_handler.status = run_task(ids, 'done')


@refresh_tasks
def custom_command() -> None:
    command = client_handler.prompt_string('Enter your command')
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
    REFRESH_TASKS = partial(refresh_tasks)
    RESET_TIMER = partial(reset_timer)
    SYNC = partial(sync)
    CUSTOM_COMMAND = partial(custom_command)

    def __call__(self, *args, **kwargs) -> None:
        gui_handler.status = ''
        self.value(*args, **kwargs)


KEY_ACTIONS = dict(zip(
    ('a', 'c', 'd', 'h', 'k', 'l', 'm', 'p', 'q', 'r', 's', 'y', '!'),
    Action.__members__.values()
))
