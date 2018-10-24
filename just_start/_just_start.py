from collections import OrderedDict
from contextlib import contextmanager
from enum import Enum, auto
from functools import wraps
from os import makedirs
from signal import signal, SIGTERM
import sys
from typing import Callable

from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, MODIFY_PROMPT, ADD_PROMPT, TASK_IDS_PROMPT,
    CUSTOM_COMMAND_PROMPT, CONFIG_DIR, UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, UNHANDLED_ERROR,
)
from ._log import log
from .pomodoro import PomodoroTimer
from .os_utils import run_task, db, get_task_list, notify

StatusWriter = Callable[[str], None]


def update_status(f: Callable[..., str]):
    @wraps(f)
    def wrapper(self: 'ActionRunner', *args, **kwargs) -> str:
        self._status_setter('')
        status = f(self, *args, **kwargs)
        self._status_setter(status)
        return status

    return wrapper


def refresh_tasks(f: Callable[..., str]):
    @wraps(f)
    def wrapper(self: 'ActionRunner', *args, **kwargs) -> str:
        out = f(self, *args, **kwargs)
        self._refresh_tasks()
        return out

    return wrapper


class ActionRunner:
    def __init__(self, pomodoro_timer: PomodoroTimer, status_setter: StatusWriter,
                 refresh_tasks: Callable):
        self._pomodoro_timer = pomodoro_timer
        self._status_setter = status_setter
        self._refresh_tasks = refresh_tasks

    def __call__(self, action: 'Action', *args, **kwargs):
        try:
            return getattr(self, action.value)(*args, **kwargs)
        except KeyboardInterrupt:
            pass

    @update_status
    @refresh_tasks
    def add(self, task_data: str) -> str:
        return run_task('add', *task_data.split())

    @update_status
    @refresh_tasks
    def delete(self, ids: str) -> str:
        return run_task(CONFIRMATION_OFF, RECURRENCE_OFF, ids, 'delete')

    @update_status
    @refresh_tasks
    def complete(self, ids: str) -> str:
        return run_task(ids, 'done')

    @update_status
    @refresh_tasks
    def modify(self, ids: str, task_data: str) -> str:
        return run_task(RECURRENCE_OFF, ids, 'modify', *task_data.split())

    @update_status
    @refresh_tasks
    def custom_command(self, command: str) -> str:
        return run_task(*command.split())

    @update_status
    def show_help(self, help_message: str = KEYBOARD_HELP) -> str:
        return help_message

    @update_status
    @refresh_tasks
    def sync(self) -> str:
        return run_task('sync')

    def toggle_timer(self):
        self._pomodoro_timer.toggle()

    def stop_timer(self):
        self._pomodoro_timer.reset()

    def refresh_tasks(self):
        return self._refresh_tasks()


class Action(Enum):
    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    ADD = auto()
    COMPLETE = auto()
    DELETE = auto()
    SHOW_HELP = auto()
    MODIFY = auto()
    TOGGLE_TIMER = auto()
    REFRESH_TASKS = auto()
    STOP_TIMER = auto()
    SYNC = auto()
    CUSTOM_COMMAND = auto()


@contextmanager
def just_start(status_writer: StatusWriter, on_tasks_refresh: Callable,
               pomodoro_status_writer: StatusWriter = notify) -> 'ActionRunner':
    def refresh_tasks_():
        on_tasks_refresh(get_task_list())

    pomodoro_timer = PomodoroTimer(notifier=pomodoro_status_writer)
    _init_just_start(refresh_tasks_, pomodoro_timer)

    with _handle_errors():
        try:
            yield ActionRunner(pomodoro_timer, status_writer, refresh_tasks_)
        finally:
            _quit_just_start(pomodoro_timer)


@contextmanager
def _handle_errors():
    try:
        yield
    except KeyboardInterrupt:
        pass
    except Exception:
        print(UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, file=sys.stderr)
        log.exception(UNHANDLED_ERROR)


def _init_just_start(refresh_tasks_: Callable, pomodoro_timer: PomodoroTimer):
    signal(SIGTERM, lambda *_, **__: _quit_just_start(pomodoro_timer))
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
    refresh_tasks_()


def _quit_just_start(pomodoro_timer: PomodoroTimer) -> None:
    db.update(pomodoro_timer.serializable_data)


NULLARY_ACTION_KEYS = OrderedDict([
    ('h', Action.SHOW_HELP),
    ('p', Action.TOGGLE_TIMER),
    ('r', Action.REFRESH_TASKS),
    ('s', Action.STOP_TIMER),
    ('y', Action.SYNC),
])
UNARY_ACTION_PROMPTS = OrderedDict([
    (Action.ADD, ADD_PROMPT),
    (Action.COMPLETE, TASK_IDS_PROMPT),
    (Action.DELETE, TASK_IDS_PROMPT),
    (Action.MODIFY, MODIFY_PROMPT),
    (Action.CUSTOM_COMMAND, CUSTOM_COMMAND_PROMPT),
])
UNARY_ACTION_KEYS = dict(zip(['a', 'c', 'd', 'm', '!'], UNARY_ACTION_PROMPTS))
assert len(UNARY_ACTION_PROMPTS) == len(UNARY_ACTION_KEYS)
# noinspection PyTypeChecker
assert len(NULLARY_ACTION_KEYS) + len(UNARY_ACTION_KEYS) == len(Action)
