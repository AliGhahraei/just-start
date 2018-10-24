from collections import OrderedDict
from contextlib import contextmanager
from enum import Enum, auto
from functools import wraps
from os import makedirs
from signal import signal, SIGTERM
from sys import stderr
from typing import Optional, Callable

from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, MODIFY_PROMPT, ADD_PROMPT, TASK_IDS_PROMPT,
    CUSTOM_COMMAND_PROMPT, CONFIG_DIR, UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, UNHANDLED_ERROR,
)
from ._log import log
from .pomodoro import PomodoroTimer
from .os_utils import run_task, UserInputError, db, get_task_list, notify

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

    def skip_phases(self, phases: Optional[str] = None) -> None:
        try:
            if phases:
                phases = int(phases)
            self._pomodoro_timer.advance_phases(phases_skipped=phases)
        except (TypeError, ValueError) as e:
            raise UserInputError('Number of phases must be a positive integer') \
                from e

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
    SKIP_PHASES = auto()
    MODIFY = auto()
    TOGGLE_TIMER = auto()
    REFRESH_TASKS = auto()
    STOP_TIMER = auto()
    SYNC = auto()
    CUSTOM_COMMAND = auto()


@contextmanager
def just_start(status_writer: StatusWriter, on_tasks_refresh: Callable,
               pomodoro_status_writer: StatusWriter = notify, pomodoro_timer: PomodoroTimer = None,
               ) -> 'ActionRunner':
    def refresh_tasks_():
        on_tasks_refresh(get_task_list())

    pomodoro_timer = pomodoro_timer or PomodoroTimer(notifier=pomodoro_status_writer)
    _init_just_start(refresh_tasks_, pomodoro_timer)
    signal(SIGTERM, lambda *_, **__: _quit_just_start(pomodoro_timer))

    with handle_errors(pomodoro_timer):
        yield ActionRunner(pomodoro_timer, status_writer, refresh_tasks_)


@contextmanager
def handle_errors(pomodoro_timer: PomodoroTimer):
    try:
        yield
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print(UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH.format(ex), file=stderr)
        log.exception(UNHANDLED_ERROR)
    finally:
        _quit_just_start(pomodoro_timer)


def _init_just_start(refresh_tasks_: Callable, pomodoro_timer: PomodoroTimer):
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


UNARY_ACTIONS = OrderedDict([
    (Action.ADD, ADD_PROMPT),
    (Action.COMPLETE, TASK_IDS_PROMPT),
    (Action.DELETE, TASK_IDS_PROMPT),
    (Action.MODIFY, MODIFY_PROMPT),
    (Action.CUSTOM_COMMAND, CUSTOM_COMMAND_PROMPT),
])
UNARY_ACTION_KEYS = dict(zip(('a', 'c', 'd', 'm', '!',),
                             UNARY_ACTIONS))
NULLARY_ACTION_KEYS = dict(zip(
    ('h', 's', 'p', 'r', 't', 'y',),
    [action for action in Action if action not in UNARY_ACTIONS]
))
