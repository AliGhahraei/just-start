import shelve
from enum import Enum
from functools import wraps, partial
from pickle import HIGHEST_PROTOCOL
from signal import signal, SIGTERM
from sys import exit
from typing import Optional, Dict, Callable, Any, Union

from .client_decorators import CLIENT_DECORATORS
from .utils import (
    client_handler, gui_handler, refresh, run_task, manage_blocked_sites,
    manage_wifi, TaskWarriorError, ActionError, JustStartError)

from .constants import (
    PHASE_SKIP_PROMPT, HELP_MESSAGE, RECURRENCE_OFF, CONFIRMATION_OFF,
    PERSISTENT_PATH)
from just_start.pomodoro import PomodoroTimer, PomodoroError


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


def write_on_error(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            func(*args, **kwargs)
        except TaskWarriorError as e:
            client_handler.write_status(str(e), error=True)

    return wrapper


def init() -> None:
    signal(SIGTERM, _signal_handler)
    pomodoro_timer.serializable_data = read_serializable_data()
    refresh()
    sync()


def read_serializable_data() -> Dict:
    try:
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
            timer_kwargs = {arg: db[arg] for arg
                            in PomodoroTimer.SERIALIZABLE_ATTRIBUTES}
    except KeyError:
        timer_kwargs = {}
    return timer_kwargs


@write_on_error
def sync() -> None:
    gui_handler.sync()


def _signal_handler() -> None:
    quit_gracefully()


def quit_gracefully() -> None:
    sync()
    manage_wifi()

    with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
        db.update(pomodoro_timer.serializable_data)
    exit()


def prompt_action_char() -> None:
    try:
        action_key = client_handler.prompt_char(
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
        client_handler.write_status(str(exc), error=True)
    except KeyboardInterrupt:
        # Cancel current action while it's still running
        pass


def input_task_ids() -> str:
    ids = client_handler.prompt_string("Enter the task's ids")

    while True:
        split_ids = ids.split(',')
        try:
            list(map(int, split_ids))
        except ValueError:
            ids = client_handler.prompt_string("Please enter valid ids",
                                               error=True)
        else:
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


def reset_timer(at_work_user_overridden: Optional[bool]=None) -> None:
    pomodoro_timer.reset(at_work_user_overridden=at_work_user_overridden)
    manage_wifi(timer_running=False)


def location_change() -> None:
    location = client_handler.prompt_string("Enter 'w' for work or anything"
                                            " else for home")
    at_work = location == 'w'
    reset_timer(at_work)
    toggle_timer()


@refresh
def add() -> None:
    name = client_handler.prompt_string("Enter the new task's data")
    gui_handler.status = run_task('add', *name.split())


@refresh
def delete() -> None:
    ids = input_task_ids()
    gui_handler.status = run_task(CONFIRMATION_OFF, RECURRENCE_OFF, ids,
                                  'delete')


@refresh
def modify() -> None:
    ids = input_task_ids()
    name = client_handler.prompt_string("Enter the modified task's data")
    gui_handler.status = run_task(RECURRENCE_OFF, ids, 'modify',
                                  *name.split())


@refresh
def complete() -> None:
    ids = input_task_ids()
    gui_handler.status = run_task(ids, 'done')


@refresh
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
