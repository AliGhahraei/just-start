#!/usr/bin/env python3

from just_start import init, client, logger


@client
def write_status(status: str, error: bool=False) -> None:
    pass


@client
def write_pomodoro_status(status: str, error: bool=False) -> None:
    pass


@client
def refresh_tasks(task_list) -> None:
    pass


@client
def prompt_char(status: str, error: bool=False) -> str:
    pass


@client
def prompt_string(status: str, error: bool=False) -> str:
    pass


@client
def read_action() -> str:
    pass
