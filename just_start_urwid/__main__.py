from functools import partial

from urwid import LineBox, Columns, TOP, Filler, MainLoop

from just_start import just_start, notify
from just_start_urwid.client import (
    TopWidget, status, on_tasks_refresh, TaskListBox, write_status,
    ActionHandler, FocusedTask, pomodoro_status, pomodoro_status_box, get_error_colors,
)


def client_notify(status: str):
    notify(status)
    pomodoro_status.set_text(status)


def main():
    task_list_box = TaskListBox()
    refresh = partial(on_tasks_refresh, task_list_box)
    with just_start(write_status, refresh, client_notify) as action_runner:
        task_list_box.action_handler = ActionHandler(action_runner, FocusedTask(task_list_box))
        task_list_box = LineBox(task_list_box, title='Tasks')
        status_box = LineBox(Filler(status, valign=TOP), title='App Status')
        columns = Columns([('weight', 1.3, task_list_box), ('weight', 1, status_box)])

        MainLoop(
            TopWidget(columns, footer=pomodoro_status_box),
            palette=(
                ('error', *get_error_colors()),
            )
        ).run()


if __name__ == '__main__':
    main()
