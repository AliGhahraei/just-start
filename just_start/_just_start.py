from collections import OrderedDict
from enum import Enum
from functools import partial
from signal import signal, SIGTERM
from typing import Dict, Optional, Callable, Any

from .client import StatusManager, refresh_tasks
from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, MODIFY_PROMPT, ADD_PROMPT,
    EXIT_MESSAGE, TASK_IDS_PROMPT, CUSTOM_COMMAND_PROMPT,
    LOCATION_CHANGE_PROMPT,
)
from .log import logger
from .pomodoro import PomodoroTimer
from .os_utils import (
    run_task, manage_wifi, block_sites, UserInputError, JustStartError, db)


UnaryCallable = Callable[[Any], Any]


def quit_just_start(*, exit_message_func: UnaryCallable,
                    sync_error_func: UnaryCallable) -> None:
    exit_message_func(EXIT_MESSAGE)
    serialize_timer()
    sync_and_manage_wifi(sync_error_func=sync_error_func)


def sync_and_manage_wifi(*, sync_error_func: UnaryCallable):
    try:
        sync()
    except JustStartError as ex:
        sync_error_func(str(ex))
    except KeyboardInterrupt:
        pass
    finally:
        manage_wifi()


def read_db_data() -> Dict:
    data = {}
    for attribute in PomodoroTimer.SERIALIZABLE_ATTRIBUTES:
        try:
            data[attribute] = db[attribute]
        except KeyError:
            logger.warning(f"Serialized attribute {attribute} couldn't be"
                           f" read (this might happen between updates)")

    if not data:
        logger.warning(f'No serialized attributes could be read')

    pomodoro_timer.serializable_data = data
    return data


status_manager = StatusManager()
pomodoro_timer = PomodoroTimer(
    lambda status: status_manager.__setattr__('pomodoro_status', status),
    block_sites
)
signal(SIGTERM, quit_just_start)


def initial_refresh_and_sync(*, sync_error_func: UnaryCallable):
    refresh_tasks()
    sync_and_manage_wifi(sync_error_func=sync_error_func)


def sync() -> None:
    status_manager.sync()


def serialize_timer() -> None:
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


def stop_timer(at_work_override: bool=False) -> None:
    pomodoro_timer.reset(at_work_override=at_work_override)
    manage_wifi(enable=False)


def location_change(location: str) -> None:
    at_work = location == 'w'
    stop_timer(at_work)
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
    REFRESH_TASKS = partial(refresh_tasks)
    STOP_TIMER = partial(stop_timer)
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
    (Action.ADD, ADD_PROMPT),
    (Action.COMPLETE, TASK_IDS_PROMPT),
    (Action.DELETE, TASK_IDS_PROMPT),
    (Action.MODIFY, MODIFY_PROMPT),
    (Action.LOCATION_CHANGE, LOCATION_CHANGE_PROMPT),
    (Action.CUSTOM_COMMAND, CUSTOM_COMMAND_PROMPT),
])
UNARY_ACTION_KEYS = dict(zip(('a', 'c', 'd', 'm', 'l', '!',),
                             UNARY_ACTIONS))
NULLARY_ACTION_KEYS = dict(zip(
    ('h', 's', 'p', 'r', 't', 'y',),
    [action for action in Action if action not in UNARY_ACTIONS]
))
