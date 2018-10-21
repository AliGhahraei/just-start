from collections import OrderedDict
from contextlib import contextmanager
from enum import Enum
from functools import partial, wraps
from os import makedirs
from signal import signal, SIGTERM
from typing import Optional, Callable, Any

from .client import StatusManager, refresh_tasks
from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, MODIFY_PROMPT, ADD_PROMPT, TASK_IDS_PROMPT,
    CUSTOM_COMMAND_PROMPT, CONFIG_DIR, UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, UNHANDLED_ERROR,
)
from ._log import log
from .pomodoro import PomodoroTimer
from .os_utils import run_task, UserInputError, db


def create_module_vars():
    status_manager_ = StatusManager()
    pomodoro_timer_ = PomodoroTimer(
        lambda status: status_manager_.__setattr__('pomodoro_status', status),
    )
    return status_manager_, pomodoro_timer_


status_manager, pomodoro_timer = create_module_vars()
UnaryCallable = Callable[[Any], Any]


@contextmanager
def just_start() -> None:
    _init_just_start()
    try:
        yield
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print(UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH.format(ex))
        log.exception(UNHANDLED_ERROR)
    finally:
        _quit_just_start()


def _init_just_start():
    data = {}
    for attribute in PomodoroTimer.SERIALIZABLE_ATTRIBUTES:
        try:
            data[attribute] = db[attribute]
        except KeyError:
            log.warning(f"Serialized attribute {attribute} couldn't be"
                        f" read (this might happen between updates)")
    if not data:
        log.warning(f'No serialized attributes could be read')
    pomodoro_timer.serializable_data = data
    makedirs(CONFIG_DIR, exist_ok=True)
    refresh_tasks()


def _quit_just_start() -> None:
    serialize_timer()


signal(SIGTERM, _quit_just_start)


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


def update_app_status(f: Callable[..., str]):
    @wraps(f)
    def wrapper(*args, **kwargs) -> str:
        status_manager.app_status = f(*args, **kwargs)
        return status_manager.app_status
    return wrapper


@update_app_status
@refresh_tasks
def add(task_data: str) -> str:
    return run_task('add', *task_data.split())


@update_app_status
@refresh_tasks
def delete(ids: str) -> str:
    return run_task(CONFIRMATION_OFF, RECURRENCE_OFF, ids, 'delete')


@update_app_status
@refresh_tasks
def modify(ids: str, task_data: str) -> str:
    return run_task(RECURRENCE_OFF, ids, 'modify', *task_data.split())


@update_app_status
@refresh_tasks
def complete(ids: str) -> str:
    return run_task(ids, 'done')


@update_app_status
@refresh_tasks
def custom_command(command: str) -> str:
    return run_task(*command.split())


@update_app_status
def show_help(help_message: str=KEYBOARD_HELP) -> str:
    return help_message


@update_app_status
@refresh_tasks
def sync() -> str:
    return run_task('sync')


class Action(Enum):
    ADD = partial(add)
    COMPLETE = partial(complete)
    DELETE = partial(delete)
    SHOW_HELP = partial(show_help)
    SKIP_PHASES = partial(skip_phases)
    MODIFY = partial(modify)
    TOGGLE_TIMER = partial(pomodoro_timer.toggle)
    REFRESH_TASKS = partial(refresh_tasks)
    STOP_TIMER = partial(pomodoro_timer.reset)
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
    (Action.CUSTOM_COMMAND, CUSTOM_COMMAND_PROMPT),
])
UNARY_ACTION_KEYS = dict(zip(('a', 'c', 'd', 'm', 'l', '!',),
                             UNARY_ACTIONS))
NULLARY_ACTION_KEYS = dict(zip(
    ('h', 's', 'p', 'r', 't', 'y',),
    [action for action in Action if action not in UNARY_ACTIONS]
))
