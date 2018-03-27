from typing import Callable

CLIENT_DECORATORS = set()


def register(function_: Callable) -> Callable:
    CLIENT_DECORATORS.add(function_.__name__)
    return function_


@register
def draw_gui() -> None: pass


@register
def write_status(status: str) -> None: print(status)


@register
def write_error(error_msg: str) -> None: print(error_msg)


@register
def write_pomodoro_status(status: str) -> None: print(status)


# noinspection PyUnusedLocal
@register
def refresh_tasks(task_list) -> None: pass


@register
def prompt_char(prompt: str) -> str: return input(prompt)


@register
def prompt_string(prompt: str) -> str: return input(prompt)


@register
def prompt_string_error(prompt: str) -> str: return input(prompt)
