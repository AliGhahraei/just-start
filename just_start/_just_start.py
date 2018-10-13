from collections import OrderedDict
from enum import Enum
from functools import partial
from os import makedirs
from signal import signal, SIGTERM
from typing import Optional, Callable, Any

from .client import StatusManager, refresh_tasks
from .constants import (
    KEYBOARD_HELP, RECURRENCE_OFF, CONFIRMATION_OFF, MODIFY_PROMPT, ADD_PROMPT,
    EXIT_MESSAGE, TASK_IDS_PROMPT, CUSTOM_COMMAND_PROMPT, CONFIG_DIR,
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


def quit_just_start(*, exit_message_func: UnaryCallable) -> None:
    exit_message_func(EXIT_MESSAGE)
    serialize_timer()


def init() -> None:
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


signal(SIGTERM, quit_just_start)


def init_gui():
    refresh_tasks()


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


def toggle_timer() -> None:
    pomodoro_timer.toggle()


def stop_timer() -> None:
    pomodoro_timer.reset()


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
    (Action.CUSTOM_COMMAND, CUSTOM_COMMAND_PROMPT),
])
UNARY_ACTION_KEYS = dict(zip(('a', 'c', 'd', 'm', 'l', '!',),
                             UNARY_ACTIONS))
NULLARY_ACTION_KEYS = dict(zip(
    ('h', 's', 'p', 'r', 't', 'y',),
    [action for action in Action if action not in UNARY_ACTIONS]
))
