#!/usr/bin/env python3

from curses import (
    wrapper, echo, noecho, cbreak, nocbreak, newwin, error, color_pair,
    init_pair, COLOR_RED, COLOR_WHITE, COLOR_GREEN, use_default_colors)
from sys import argv
from typing import Any

from core import log_failure, start, GuiHandler, PromptHandler


class CursesGuiHandler(GuiHandler):
    @staticmethod
    def newborderedwin(height: int, width: int, start_y: int, start_x: int,
                       title: str='') -> Any:
        borderedwindow = newwin(height, width, start_y, start_x)
        borderedwindow.clear()
        borderedwindow.border()
        borderedwindow.move(0, 2)
        borderedwindow.addstr(title)
        borderedwindow.refresh()

        return newwin(height - 2, width - 2, start_y + 1, start_x + 1)

    def __init__(self, stdscr: Any):
        self.stdscr = stdscr

        use_default_colors()
        for color in COLOR_WHITE, COLOR_GREEN, COLOR_RED:
            init_pair(color, color, -1)

        self.task_window = None

        self.pomodoro_window = None
        self.written_pomodoro_status = ''

        self.status_window = None
        self.written_status = ''
        self.status_color = COLOR_WHITE

        self.prompt_handler = CursesPromptHandler(self.stdscr)

    def draw_gui(self) -> None:
        self.stdscr.refresh()

        max_y, max_x = self.stdscr.getmaxyx()
        pomodoro_window_height = 5
        task_window_height = max_y - pomodoro_window_height
        task_window_width = int(max_x / 2)

        self.task_window = self.newborderedwin(task_window_height,
                                               task_window_width, 0, 0)
        self.refresh_tasks()

        self.status_window = self.newborderedwin(task_window_height,
                                                 task_window_width,
                                                 0,
                                                 task_window_width,
                                                 'App status')

        prompt_y = task_window_height
        self.prompt_handler.draw_prompt_windows(prompt_y,
                                                pomodoro_window_height,
                                                task_window_width,
                                                self.status_window)

        self.pomodoro_window = self.newborderedwin(pomodoro_window_height,
                                                   task_window_width,
                                                   task_window_height,
                                                   task_window_width,
                                                   'Pomodoro status')

        self.write_pomodoro_status(self.written_pomodoro_status)
        self.write_status(self.written_status, color=self.status_color)

    def write_error(self, error_msg: str):
        self.write_status(error_msg, color=COLOR_RED)

    def write_status(self, status: str, color=COLOR_WHITE) -> None:
        self.prompt_handler.write_prompt('')
        self.status_window.clear()
        self.status_window.addstr(status, color_pair(color))
        self.status_window.refresh()
        self.written_status = status
        self.status_color = color

    def write_pomodoro_status(self, status: str) -> None:
        self.status_window.clear()
        self.pomodoro_window.clear()
        self.pomodoro_window.addstr(status)
        self.pomodoro_window.refresh()
        self.written_pomodoro_status = status

    def refresh_tasks(self) -> None:
        self.task_window.clear()

        try:
            for y, task in enumerate(self.task_list):
                self.task_window.addstr(y, 1, task)
        except error:
            pass

        self.task_window.refresh()


class CursesPromptHandler(PromptHandler):
    def __init__(self, stdscr: Any):
        self.stdscr = stdscr
        self.prompt_color = COLOR_WHITE

        self.status_window = self.prompt_window = None
        self.input_window = None

    def draw_prompt_windows(self, prompt_y: int, prompt_height: int,
                            prompt_width: int, status_window: Any) -> None:
        CursesGuiHandler.newborderedwin(prompt_height, prompt_width, prompt_y,
                                        0)

        self.prompt_window = newwin(1, prompt_width - 2,
                                    prompt_y + 1, 1)

        self.input_window = newwin(prompt_height - 3,  prompt_width - 2,
                                   prompt_y + 2, 1)

        self.status_window = status_window

        self.input_window.refresh()
        self.prompt_window.refresh()

    def write_prompt(self, prompt: str) -> None:
        self.status_window.clear()
        self.prompt_window.clear()
        self.prompt_window.addstr(prompt)
        self.prompt_window.refresh()

    def prompt_char(self, status: str, color: int=COLOR_WHITE) -> str:
        self.write_prompt(status)
        self.input_window.clear()
        return self.input_window.getkey(
            *self.input_window.getyx()
        )

    def prompt_string(self, status: str, color: int=COLOR_WHITE) -> str:
        self.write_prompt(status + " and press Ctrl-Enter when done (or "
                          "Ctrl-C to cancel)")
        self.input_window.clear()

        try:
            echo()
            nocbreak()
            key_sequence = self.input_window.getstr(
                *self.input_window.getyx())
        finally:
            noecho()
            cbreak()
        return key_sequence.decode('utf-8')

    def prompt_string_error(self, error_msg: str) -> str:
        return self.prompt_string(error_msg, color=COLOR_RED)


def main() -> None:
    try:
        wrapper(start_curses)
    except error as e:
        log_failure(e, f'An error occurred while drawing {argv[0]}. My best'
                       f' guess is that the window was too small.')
    except Exception as e:
        log_failure(e, f'Unhandled error.')


def start_curses(stdscr: Any) -> None:
    stdscr.clear()
    gui_handler = CursesGuiHandler(stdscr)
    start(gui_handler, gui_handler.prompt_handler)


if __name__ == '__main__':
    main()
