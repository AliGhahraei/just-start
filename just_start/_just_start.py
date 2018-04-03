import shelve
from collections import OrderedDict
from enum import Enum
from functools import partial
from pickle import HIGHEST_PROTOCOL
from signal import signal, SIGTERM
from sys import exit
from typing import Dict, List, Optional

from .constants import (
    KEYBOARD_HELP_MESSAGE, RECURRENCE_OFF, CONFIRMATION_OFF,
    PERSISTENT_PATH)
from .log import logger
from .pomodoro import PomodoroTimer
from .utils import (
    client, StatusManager, refresh_tasks, run_task, manage_wifi,
    block_sites, JustStartError, UserInputError, TaskWarriorError)


status_manager = StatusManager()
pomodoro_timer = PomodoroTimer(
    lambda status: status_manager.__setattr__('pomodoro_status', status),
    block_sites
)


def init(ignore_sync_fail=True) -> None:
    """Initialize the just-start program.

    :param ignore_sync_fail: False raises a TaskWarriorError on sync fail
    :raise TaskWarriorError if sync fails and ignore_sync_fail is False
    """
    read_serialized_data()
    handle_sigterm()
    try:
        refresh_tasks_and_sync()
    except TaskWarriorError:
        if not ignore_sync_fail:
            raise


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


def skip_phases(phases: Optional[int]=None) -> None:
    try:
        pomodoro_timer.advance_phases(phases_skipped=phases)
    except (TypeError, ValueError) as e:
        raise UserInputError('Number of phases must be a positive integer') \
            from e

    manage_wifi(timer_running=True)


def toggle_timer() -> None:
    pomodoro_timer.toggle()
    manage_wifi(pomodoro_timer.is_running)


def reset_timer(at_work_override: bool=False) -> None:
    pomodoro_timer.reset(at_work_override=at_work_override)
    manage_wifi(timer_running=False)


def location_change(location: str) -> None:
    at_work = location == 'w'
    reset_timer(at_work)
    toggle_timer()


@refresh_tasks
def add(task_data: str) -> None:
    status_manager.app_status = run_task('add', *task_data.split())


@refresh_tasks
def delete(ids: List[str]) -> None:
    status_manager.app_status = run_task(CONFIRMATION_OFF, RECURRENCE_OFF,
                                         ','.join(ids), 'delete')


@refresh_tasks
def modify(ids: List[str], task_data: str) -> None:
    status_manager.app_status = run_task(RECURRENCE_OFF, ','.join(ids),
                                         'modify', *task_data.split())


@refresh_tasks
def complete(ids: List[str]) -> None:
    status_manager.app_status = run_task(','.join(ids), 'done')


@refresh_tasks
def custom_command(command: str) -> None:
    status_manager.app_status = run_task(*command.split())


def show_help(help_message: str=KEYBOARD_HELP_MESSAGE) -> None:
    status_manager.app_status = help_message


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
    STOP_TIMER = partial(reset_timer)
    SYNC = partial(sync)
    CUSTOM_COMMAND = partial(custom_command)

    def __call__(self, *args, **kwargs) -> None:
        status_manager.app_status = ''
        try:
            self.value(*args, **kwargs)
        except KeyboardInterrupt:
            # Cancel current action while it's still running
            pass


UNARY_ACTION_KEYS = OrderedDict([
    ('c', Action.COMPLETE), ('d', Action.DELETE,), ('m', Action.MODIFY)
])
NULLARY_ACTION_KEYS = dict(zip(
    ('a', 'h', 'k', 'l', 'p', 'q', 'r', 's', 'y', '!'),
    [action for action in Action if action not in UNARY_ACTION_KEYS.values()]
))
