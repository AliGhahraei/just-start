#!/usr/bin/env python3

from curses import (
    wrapper, echo, noecho, cbreak, nocbreak, newwin, error, color_pair,
    init_pair, COLOR_RED, COLOR_WHITE, COLOR_GREEN, use_default_colors)
from sys import argv
from traceback import format_exc
from typing import Any

from just_start import main as just_start_main, client, logger


class CursesClient:
    # noinspection SpellCheckingInspection
    def __init__(self) -> None:
        self._stdscr = None
        self.task_window = None
        self.pomodoro_window = None
        self.status_window = None
        self.prompt_window = None
        self.input_window = None

    @property
    def stdscr(self) -> None:
        return self._stdscr

    @stdscr.setter
    def stdscr(self, value) -> None:
        self._stdscr = value
        use_default_colors()
        for color in COLOR_WHITE, COLOR_GREEN, COLOR_RED:
            init_pair(color, color, -1)

    # noinspection SpellCheckingInspection
    @staticmethod
    def newborderedwin(height: int, width: int, start_y: int, start_x: int,
                       title: str='') -> Any:
        bordered_window = newwin(height, width, start_y, start_x)
        bordered_window.clear()
        bordered_window.border()
        bordered_window.move(0, 2)
        bordered_window.addstr(title)
        bordered_window.refresh()

        return newwin(height - 2, width - 2, start_y + 1, start_x + 1)

    def draw_prompt_windows(self, prompt_y: int, prompt_height: int,
                            prompt_width: int, status_window: Any) -> None:
        curses.newborderedwin(prompt_height, prompt_width, prompt_y, 0)

        self.prompt_window = newwin(1, prompt_width - 2,
                                    prompt_y + 1, 1)

        self.input_window = newwin(prompt_height - 3,  prompt_width - 2,
                                   prompt_y + 2, 1)

        self.status_window = status_window

        self.input_window.refresh()
        self.prompt_window.refresh()

    def write_prompt(self, prompt: str, color: int=COLOR_WHITE) -> None:
        self.status_window.clear()
        self.prompt_window.clear()
        self.prompt_window.addstr(prompt, color)
        self.prompt_window.refresh()


curses = CursesClient()


def main() -> None:
    try:
        wrapper(start_curses)
    except error:
        logger.critical(format_exc())
        exit(f'An error occurred while drawing {argv[0]}. The window was'
             f' probably too small.')


# noinspection SpellCheckingInspection
@just_start_main
def start_curses(stdscr: Any) -> None:
    stdscr.clear()
    curses.stdscr = stdscr


if __name__ == '__main__':
    main()


@client
def draw_gui() -> None:
    curses.stdscr.refresh()

    max_y, max_x = curses.stdscr.getmaxyx()
    pomodoro_window_height = 5
    task_window_height = max_y - pomodoro_window_height
    task_window_width = int(max_x / 2)

    curses.task_window = curses.newborderedwin(task_window_height,
                                               task_window_width, 0, 0)

    curses.status_window = curses.newborderedwin(task_window_height,
                                                 task_window_width,
                                                 0,
                                                 task_window_width,
                                                 'App status')

    prompt_y = task_window_height
    curses.draw_prompt_windows(prompt_y,
                               pomodoro_window_height,
                               task_window_width,
                               curses.status_window)

    curses.pomodoro_window = curses.newborderedwin(pomodoro_window_height,
                                                   task_window_width,
                                                   task_window_height,
                                                   task_window_width,
                                                   'Pomodoro status')


@client
def write_error(error_msg: str):
    write_status(error_msg, color=COLOR_RED)


@client
def write_status(status: str, color=COLOR_WHITE) -> None:
    curses.write_prompt('')
    curses.status_window.clear()
    curses.status_window.addstr(status, color_pair(color))
    curses.status_window.refresh()


@client
def write_pomodoro_status(status: str) -> None:
    curses.status_window.clear()
    curses.pomodoro_window.clear()
    curses.pomodoro_window.addstr(status)
    curses.pomodoro_window.refresh()


@client
def refresh_tasks(task_list) -> None:
    curses.task_window.clear()

    try:
        for y, task in enumerate(task_list):
            curses.task_window.addstr(y, 1, task)
    except error:
        pass

    curses.task_window.refresh()


@client
def prompt_char(status: str, color: int=COLOR_WHITE) -> str:
    curses.write_prompt(status, color)
    curses.input_window.clear()
    return curses.input_window.getkey(*curses.input_window.getyx())


@client
def prompt_string(status: str, color: int=COLOR_WHITE) -> str:
    curses.write_prompt(f"{status} and press Ctrl-Enter when done (or Ctrl-C"
                        f" to cancel)", color)
    curses.input_window.clear()

    try:
        echo()
        nocbreak()
        key_sequence = curses.input_window.getstr(*curses.input_window.getyx())
    finally:
        noecho()
        cbreak()
    return key_sequence.decode('utf-8')


@client
def prompt_string_error(error_msg: str) -> str:
    return prompt_string(error_msg, color=COLOR_RED)
