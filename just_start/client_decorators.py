from typing import Callable

CLIENT_DECORATORS = set()


def _register(function_: Callable) -> Callable:
    CLIENT_DECORATORS.add(function_.__name__)
    return function_


# noinspection PyUnusedLocal
@_register
def write_status(status: str, error: bool=False) -> None: pass


# noinspection PyUnusedLocal
@_register
def write_pomodoro_status(status: str, error: bool=False) -> None: pass


# noinspection PyUnusedLocal
@_register
def prompt_char(prompt: str, error: bool=False) -> str: pass


# noinspection PyUnusedLocal
@_register
def prompt_string(prompt: str, error: bool=False) -> str: pass


# noinspection PyUnusedLocal
@_register
def on_tasks_refresh(task_list) -> None: pass
