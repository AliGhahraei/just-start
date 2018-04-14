#!/usr/bin/env python3
from typing import List, Union, Tuple

from urwid import (
    Text, ListBox, SimpleFocusListWalker, MainLoop, Edit, LineBox, Frame,
    Filler, Columns, TOP, ExitMainLoop
)

from just_start import (
    client, initial_refresh_and_sync, get_client_config,
    NULLARY_ACTION_KEYS, UNARY_ACTION_KEYS, UNARY_ACTIONS,
    JustStartError, UserInputError, PromptSkippedPhases, Action, quit_just_start
)
from just_start.constants import (
    INVALID_ACTION_KEY, SKIPPED_PHASES_PROMPT
)


pomodoro_status = Text('')
status = Text('')


class TaskListBox(ListBox):
    def __init__(self):
        body = SimpleFocusListWalker([])
        super().__init__(body)
        self.action = None
        self.prev_caption = None

    def keypress(self, size: int, key: str):
        if self.action:
            if key == 'enter':
                self.run_unary_action()
            elif key == 'esc':
                self.clear_edit_text_and_action()
                self.focus.set_caption(self.prev_caption)
            elif key not in ('up', 'down'):
                return super().keypress(size, key)

        elif key == 'q':
            quit_just_start(exit_message_func=write_status,
                            sync_error_func=error)
            raise ExitMainLoop()

        elif key in ('down', 'j'):
            return super().keypress(size, 'down')

        elif key in ('up', 'k'):
            return super().keypress(size, 'up')

        else:
            try:
                self.read_action(key)
            except JustStartError as e:
                error(str(e))

    def clear_edit_text_and_action(self):
        self.action = None
        self.focus.edit_text = ''

    def run_unary_action(self):
        user_input = self.focus.edit_text
        try:
            if self.action is Action.MODIFY:
                self.action(self.focus.id, user_input)
            else:
                self.action(user_input)
        finally:
            if (self.action in UNARY_ACTIONS
                    or self.action is Action.SKIP_PHASES):
                self.focus.set_caption(self.prev_caption)

            self.clear_edit_text_and_action()

    def read_action(self, key: str):
        try:
            action = NULLARY_ACTION_KEYS[key]
        except KeyError:
            try:
                action = UNARY_ACTION_KEYS[key]
            except KeyError:
                raise UserInputError(f'{INVALID_ACTION_KEY} "{key}"')

            if action in (Action.DELETE, Action.COMPLETE):
                action(self.focus.id)
            else:
                prompt_message = UNARY_ACTIONS[action]
                self.set_caption_and_action(prompt_message, action)
        else:
            try:
                action()
            except PromptSkippedPhases:
                self.set_caption_and_action(SKIPPED_PHASES_PROMPT, action)

    def set_caption_and_action(self, caption: str, action: Action):
        self.prev_caption = self.focus.caption
        self.focus.set_caption(f'{self.prev_caption}\n{caption} ')
        self.action = action


def error(status_: str):
    write_status(('error', status_))


task_list = TaskListBox()


@client
def write_status(status_: Union[str, Tuple[str, str]]) -> None:
    status.set_text(status_)


@client
def write_pomodoro_status(status_: str) -> None:
    pomodoro_status.set_text(status_)


class Task(Edit):
    def __init__(self, caption: str='', **kwargs):
        self.id = caption.split()[0] if caption else None
        super().__init__(caption=caption, **kwargs)


@client
def on_tasks_refresh(task_list_: List[str]) -> None:
    task_list.body = SimpleFocusListWalker([
        Task(task) for task in task_list_[4:]
    ])


task_list_box = LineBox(task_list, title='Tasks')
status_box = LineBox(Filler(status, valign=TOP), title='App Status')
pomodoro_status_box = LineBox(pomodoro_status, title='Pomodoro Status')


class TopWidget(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial_refresh_and_sync(sync_error_func=error)


columns = Columns([('weight', 1.3, task_list_box), ('weight', 1, status_box)])
top = TopWidget(columns, footer=pomodoro_status_box)


def main():
    client_config = get_client_config('just_start_urwid')
    error_fg = client_config.get('error_fg', 'dark red')
    error_bg = client_config.get('error_bg', '')

    # noinspection PyBroadException
    try:
        MainLoop(top, palette=(
            ('error', error_fg, error_bg),
        )).run()
    except KeyboardInterrupt:
        quit_just_start(exit_message_func=print, sync_error_func=exit)
    except Exception as e:
        print(f'Unhandled error: {e}')
        quit_just_start(exit_message_func=print, sync_error_func=exit)


if __name__ == '__main__':
    main()
