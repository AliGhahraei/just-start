import atexit
import shelve
from collections import OrderedDict
from enum import Enum
from functools import partial
from pickle import HIGHEST_PROTOCOL
from signal import signal, SIGTERM
from typing import Dict, Optional, Callable, Any

from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, PERSISTENT_PATH
)
from .log import logger
from .pomodoro import PomodoroTimer
from .utils import (
    StatusManager, refresh_tasks, run_task, manage_wifi, block_sites,
    UserInputError, JustStartError)


def quit_gracefully() -> None:
    serialize_timer()
    try:
        sync()
    except JustStartError as ex:
        print(str(ex))
    finally:
        manage_wifi()


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


status_manager = StatusManager()
pomodoro_timer = PomodoroTimer(
    lambda status: status_manager.__setattr__('pomodoro_status', status),
    block_sites
)
atexit.register(quit_gracefully)
signal(SIGTERM, quit_gracefully)
read_serialized_data()


def initial_refresh_and_sync(*, error: Callable[[str], Any]):
    refresh_tasks()
    try:
        sync()
    except JustStartError as e:
        error(str(e))
    finally:
        manage_wifi()


def sync() -> None:
    status_manager.sync()


def serialize_timer() -> None:
    with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
        db.update(pomodoro_timer.serializable_data)


def skip_phases(phases: Optional[str]=None) -> None:
    try:
        if phases:
            phases = int(phases)
        pomodoro_timer.advance_phases(phases_skipped=phases)
    except (TypeError, ValueError) as e:
        raise UserInputError('Number of phases must be a positive integer') \
            from e

    manage_wifi(enable=True)


def toggle_timer() -> None:
    pomodoro_timer.toggle()
    manage_wifi(enable=pomodoro_timer.is_running)


def reset_timer(at_work_override: bool=False) -> None:
    pomodoro_timer.reset(at_work_override=at_work_override)
    manage_wifi(enable=False)


def location_change(location: str) -> None:
    at_work = location == 'w'
    reset_timer(at_work)
    toggle_timer()


@refresh_tasks
def add(task_data: str) -> None:
    status_manager.app_status = run_task('add', *task_data.split())


@refresh_tasks
def delete(ids: str) -> None:
    status_manager.app_status = run_task(CONFIRMATION_OFF, RECURRENCE_OFF,
                                         ids, 'delete')


@refresh_tasks
def modify(ids: str, task_data: str) -> None:
    status_manager.app_status = run_task(RECURRENCE_OFF, ids,
                                         'modify', *task_data.split())


@refresh_tasks
def complete(ids: str) -> None:
    status_manager.app_status = run_task(ids, 'done')


@refresh_tasks
def custom_command(command: str) -> None:
    status_manager.app_status = run_task(*command.split())


def show_help(help_message: str=KEYBOARD_HELP) -> None:
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
    QUIT = partial(quit)
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


UNARY_ACTIONS = OrderedDict([
    (Action.ADD, "Enter the task's data"),
    (Action.COMPLETE, "Enter the tasks' ids"),
    (Action.DELETE, "Enter the tasks' ids"),
    (Action.MODIFY, "Enter the tasks' ids"),
    (Action.LOCATION_CHANGE, "Enter 'w' for work or anything else for home"),
    (Action.CUSTOM_COMMAND, "Enter your custom command"),
])
UNARY_ACTION_KEYS = dict(zip(('a', 'c', 'd', 'm', 'l', '!',), UNARY_ACTIONS))
NULLARY_ACTION_KEYS = dict(zip(
    ('h', 'k', 'p', 'q', 'r', 's', 'y',),
    [action for action in Action if action not in UNARY_ACTIONS]
))
