#!/usr/bin/env python3
from contextlib import contextmanager
from typing import List, Union, Tuple, Type, Any, Callable, Dict

from urwid import (
    Text, ListBox, SimpleFocusListWalker, Edit, LineBox, Frame, Filler, Columns, TOP, ExitMainLoop,
    MainLoop,
)

from just_start import (
    client, init_gui, get_client_config, NULLARY_ACTION_KEYS, UNARY_ACTION_KEYS, UNARY_ACTIONS,
    quit_just_start, JustStartError, UserInputError, PromptSkippedPhases, Action, init, log,
)
from just_start import constants as const


IGNORED_KEYS_DURING_ACTION = ('up', 'down')

pomodoro_status = Text('')
status = Text('')


class ActionNotInProgress(Exception):
    pass


class ActionRunner:
    def __init__(self, focused_task: 'FocusedTask'):
        self.action = None
        self.prev_caption = None
        self.focused_task = focused_task

        self.key_handlers = {
            'enter': self._run_unary_action_or_write_error,
            'esc': self._cancel_action,
            **{key: lambda: None for key in IGNORED_KEYS_DURING_ACTION}
        }

    def handle_key_for_action(self, key: str) -> bool:
        if self.action is None:
            raise ActionNotInProgress

        try:
            handler = self.key_handlers[key]
        except KeyError:
            return False

        handler()
        return True

    def _run_unary_action_or_write_error(self):
        try:
            self._run_unary_action()
        except JustStartError as e:
            error(str(e))

    def _cancel_action(self):
        self._clear_edit_text_and_action()
        self.focused_task.set_caption(self.prev_caption)

    def _run_unary_action(self):
        user_input = self.focused_task.edit_text
        try:
            if self.action is Action.MODIFY:
                self.action(self.focused_task.task_id, user_input)
            else:
                try:
                    self.action(user_input)
                except JustStartError as e:
                    error(str(e))
        finally:
            if (self.action in UNARY_ACTIONS
                    or self.action is Action.SKIP_PHASES):
                self.focused_task.set_caption(self.prev_caption)

            self._clear_edit_text_and_action()

    def _clear_edit_text_and_action(self):
        self.action = None
        self.focused_task.edit_text = ''

    def start_action(self, key: str):
        try:
            self._read_action(key)
        except JustStartError as e:
            error(str(e))

    def _read_action(self, key: str):
        try:
            action = NULLARY_ACTION_KEYS[key]
        except KeyError:
            try:
                action = UNARY_ACTION_KEYS[key]
            except KeyError:
                raise UserInputError(f'{const.INVALID_ACTION_KEY} "{key}"')

            if action in (Action.DELETE, Action.COMPLETE):
                action(self.focused_task.task_id)
            else:
                prompt_message = UNARY_ACTIONS[action]
                self._set_caption_and_action(prompt_message, action)
        else:
            try:
                action()
            except PromptSkippedPhases:
                self._set_caption_and_action(const.SKIPPED_PHASES_PROMPT, action)

    def _set_caption_and_action(self, caption: str, action: Action):
        self.prev_caption = self.focused_task.caption
        self.focused_task.set_caption(f'{self.prev_caption}\n{caption} ')
        self.action = action


class FocusedTask:
    def __init__(self, task_list: 'TaskListBox'):
        super().__setattr__('task_list', task_list)

    def __getattr__(self, item: str):
        return getattr(self.task_list.focus, item)

    def __setattr__(self, key: str, value: Any):
        return setattr(self.task_list.focus, key, value)


class TaskListBox(ListBox):
    def __init__(self, action_runner: ActionRunner = None):
        body = SimpleFocusListWalker([])
        super().__init__(body)
        self.action_runner = action_runner or ActionRunner(FocusedTask(self))

    def keypress(self, size: int, key: str):
        if key == 'q':
            quit_just_start(exit_message_func=write_status)
            raise ExitMainLoop()
        if key in ('down', 'j'):
            return super().keypress(size, 'down')
        if key in ('up', 'k'):
            return super().keypress(size, 'up')
        try:
            if not self.action_runner.handle_key_for_action(key):
                return super().keypress(size, key)
        except ActionNotInProgress:
            self.action_runner.start_action(key)


def error(status_: str):
    write_status(('error', status_))


@client
def write_status(status_: Union[str, Tuple[str, str]]) -> None:
    status.set_text(status_)


@client
def write_pomodoro_status(status_: str) -> None:
    pomodoro_status.set_text(status_)


class TaskWidget(Edit):
    def __init__(self, caption: str='', **kwargs):
        self._task_id = caption.split()[0] if caption else None
        super().__init__(caption=caption, **kwargs)

    @property
    def task_id(self):
        return self._task_id

    @task_id.setter
    def task_id(self, task_id: str):
        self._task_id = task_id


task_list = TaskListBox()


@client
def on_tasks_refresh(task_list_: List[str]) -> None:
    task_list.body = SimpleFocusListWalker([
        TaskWidget(task) for task in task_list_[4:]
    ])


task_list_box = LineBox(task_list, title='Tasks')
status_box = LineBox(Filler(status, valign=TOP), title='App Status')
pomodoro_status_box = LineBox(pomodoro_status, title='Pomodoro Status')


class TopWidget(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init()
        init_gui()


columns = Columns([('weight', 1.3, task_list_box), ('weight', 1, status_box)])
top = TopWidget(columns, footer=pomodoro_status_box)


def get_error_colors(client_config_getter: Callable[[str], Dict[str, str]] = get_client_config) \
        -> Tuple[str, str]:
    client_config = client_config_getter('just_start_urwid')
    error_fg = client_config.get('error_fg', 'dark red')
    error_bg = client_config.get('error_bg', '')
    return error_fg, error_bg


@contextmanager
def handle_loop_exceptions():
    try:
        yield
    except KeyboardInterrupt:
        quit_just_start(exit_message_func=print)
    except Exception as ex:
        print(const.UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH.format(ex))
        log.exception(const.UNHANDLED_ERROR)
        quit_just_start(exit_message_func=print)


def create_main_loop(loop_class: Type = MainLoop) -> MainLoop:
    return loop_class(
        top,
        palette=(
            ('error', *get_error_colors()),
        )
    )
