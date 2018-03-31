#!/usr/bin/env python3

from just_start import init, client, logger, prompt_and_exec_action


@client
def write_status(status: str, error: bool=False) -> None:
    pass


@client
def write_pomodoro_status(status: str, error: bool=False) -> None:
    pass


@client
def prompt_char(status: str, error: bool=False) -> str:
    pass


@client
def prompt_string(status: str, error: bool=False) -> str:
    pass


@client
def on_tasks_refresh(task_list) -> None:
    pass
