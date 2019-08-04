from collections import OrderedDict
from contextlib import contextmanager
from enum import Enum, auto
from functools import wraps
from os import makedirs
from signal import signal, SIGTERM
import sys
from threading import Timer
from typing import Callable, Generator

from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, MODIFY_PROMPT, ADD_PROMPT, TASK_IDS_PROMPT,
    CUSTOM_COMMAND_PROMPT, CONFIG_DIR, UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, UNHANDLED_ERROR,
)
from just_start.logging import logger
from just_start.pomodoro import PomodoroTimer, StatusWriter, PomodoroSerializer
from just_start.os_utils import run_task, db, get_task_list, notify


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
               pomodoro_status_writer: StatusWriter = notify) \
        -> Generator['ActionRunner', None, None]:
    def refresh_tasks_():
        on_tasks_refresh(get_task_list())

    pomodoro_timer = PomodoroTimer(notifier=pomodoro_status_writer, timer=TimerRunner())
    pomodoro_serializer = _init_just_start(refresh_tasks_, pomodoro_timer)

    with _handle_errors():
        try:
            yield ActionRunner(pomodoro_timer, status_writer, refresh_tasks_)
        finally:
            _quit_just_start(pomodoro_serializer)


class TimerRunner:
    def __init__(self):
        self.timer = None

    def start(self, seconds: int, callback: Callable[[], None]):
        self.timer = Timer(seconds, callback)
        self.timer.start()

    def stop(self):
        self.timer.cancel()


def _init_just_start(refresh_tasks_: Callable, pomodoro_timer: PomodoroTimer) -> PomodoroSerializer:
    pomodoro_serializer = PomodoroSerializer(pomodoro_timer)
    pomodoro_serializer.set_serialized_timer_data(db)
    signal(SIGTERM, lambda *_, **__: _quit_just_start(pomodoro_serializer))
    makedirs(CONFIG_DIR, exist_ok=True)
    refresh_tasks_()
    return pomodoro_serializer


def _quit_just_start(pomodoro_serializer: PomodoroSerializer) -> None:
    db.update(pomodoro_serializer.serializable_data)


@contextmanager
def _handle_errors():
    try:
        yield
    except KeyboardInterrupt:
        pass
    except Exception:
        print(UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, file=sys.stderr)
        logger.exception(UNHANDLED_ERROR)


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
