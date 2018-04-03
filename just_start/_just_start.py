import shelve
from enum import Enum
from functools import wraps, partial
from pickle import HIGHEST_PROTOCOL
from signal import signal, SIGTERM
from sys import exit
from typing import Dict, List, Callable

from .constants import (
    PHASE_SKIP_PROMPT, KEYBOARD_HELP_MESSAGE, RECURRENCE_OFF, CONFIRMATION_OFF,
    PERSISTENT_PATH)
from .log import logger
from .pomodoro import PomodoroTimer, PomodoroError
from .utils import (
    client, StatusManager, refresh_tasks, run_task, manage_wifi,
    block_sites, JustStartError, UserInputError,
    PromptKeyboardInterrupt)


status_manager = StatusManager()
pomodoro_timer = PomodoroTimer(
    lambda status: status_manager.__setattr__('pomodoro_status', status),
    block_sites
)
Prompt = Callable[[str], str]


def write_errors_option(func):
    @wraps(func)
    def wrapper(*args, write_errors=True, **kwargs):
        if write_errors:
            try:
                func(*args, **kwargs)
            except JustStartError as e:
                client.write_status(str(e), error=True)
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
    except (KeyError, AttributeError) as e:
        logger.warning(f"Serialized data couldn't be read: {str(e)}")
        data = {}

    pomodoro_timer.serializable_data = data
    return data


def handle_sigterm():
    signal(SIGTERM, _signal_handler)


def refresh_tasks_and_sync():
    refresh_tasks()
    sync()


def sync() -> None:
    status_manager.sync()


# noinspection PyUnusedLocal
@write_errors_option
def prompt_action(prompt: Prompt, write_errors=True) -> 'Action':
    try:
        action_key = prompt('Waiting for user. Pressing h shows available'
                            ' actions')
    except KeyboardInterrupt as e:
        raise PromptKeyboardInterrupt(f'Ctrl+C was pressed with no action'
                                      f' selected. Use q to quit') from e
    else:
        try:
            action = KEY_ACTIONS[action_key]
        except KeyError as e:
            raise UserInputError(f'Unknown action key: "{action_key}"') from e
        else:
            return action


def _signal_handler() -> None:
    quit_gracefully()


def quit_gracefully() -> None:
    try:
        sync()
    except JustStartError as e:
        client.write_status(str(e), error=True)
    manage_wifi()
    serialize_timer()
    exit()


def serialize_timer() -> None:
    with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
        db.update(pomodoro_timer.serializable_data)


def input_task_ids(prompt: Prompt) -> str:
    ids = prompt("Enter the task's ids")

    split_ids = ids.split(',')
    try:
        list(map(int, split_ids))
    except ValueError as e:
        raise UserInputError(f'Invalid id list "{ids}"') from e

    return ids


def skip_phases(prompt: Prompt) -> None:
    if pomodoro_timer.phase is not pomodoro_timer.phase.WORK:
        pomodoro_timer.advance_phases()
    elif not pomodoro_timer.skip_enabled:
        raise PomodoroError('Sorry, please work 1 pomodoro to re-enable phase'
                            ' skipping')
    else:
        prompt_message = PHASE_SKIP_PROMPT
        valid_phases = False

        while not valid_phases:
            try:
                phases = int(prompt(prompt_message))
            except ValueError:
                pass
            else:
                if phases >= 1:
                    pomodoro_timer.advance_phases(phases_skipped=phases)
                    valid_phases = True
                    manage_wifi(timer_running=True)

            prompt_message = 'Please enter a valid number of phases'


def toggle_timer() -> None:
    pomodoro_timer.toggle()
    manage_wifi(pomodoro_timer.is_running)


def reset_timer(at_work_override: bool=False) -> None:
    pomodoro_timer.reset(at_work_override=at_work_override)
    manage_wifi(timer_running=False)


def location_change(prompt: Prompt) -> None:
    location = prompt("Enter 'w' for work or anything else for home")
    at_work = location == 'w'
    reset_timer(at_work)
    toggle_timer()


@refresh_tasks
def add(prompt: Prompt) -> None:
    name = prompt("Enter the new task's data")
    status_manager.app_status = run_task('add', *name.split())


@refresh_tasks
def delete(ids: List[str]) -> None:
    status_manager.app_status = run_task(CONFIRMATION_OFF, RECURRENCE_OFF,
                                         ','.join(ids), 'delete')


@refresh_tasks
def modify(ids: List[str], prompt: Prompt) -> None:
    name = prompt("Enter the modified data")
    status_manager.app_status = run_task(RECURRENCE_OFF, ','.join(ids),
                                         'modify', *name.split())


@refresh_tasks
def complete(ids: List[str]) -> None:
    status_manager.app_status = run_task(','.join(ids), 'done')


@refresh_tasks
def custom_command(prompt: Prompt) -> None:
    command = prompt('Enter your command')
    status_manager.app_status = run_task(*command.split())


def show_help(help_message: str=KEYBOARD_HELP_MESSAGE) -> None:
    status_manager.app_status = help_message


class Action(Enum):
    ADD = partial(add)
    COMPLETE = partial(complete)
    DELETE = partial(delete)
    SHOW_HELP = partial(show_help)
    INPUT_TASK_IDS = partial(input_task_ids)
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
        status_manager.app_status = ''
        try:
            self.value(*args, **kwargs)
        except KeyboardInterrupt:
            # Cancel current action while it's still running
            pass


KEY_ACTIONS = dict(zip(
    ('a', 'c', 'd', 'h', 'i', 'k', 'l', 'm', 'p', 'q', 'r', 's', 'y', '!'),
    Action.__members__.values()
))
