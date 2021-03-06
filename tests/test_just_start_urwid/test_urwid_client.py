from unittest.mock import create_autospec, patch

from pytest import fixture, raises, mark

from just_start import (
    UNARY_ACTION_PROMPTS, NULLARY_ACTION_KEYS, UNARY_ACTION_KEYS, UserInputError, Action,
    ActionRunner,
)
from just_start.pomodoro import PomodoroTimer
from just_start_urwid.client import (
    ActionHandler, ActionNotInProgress, TaskWidget, IGNORED_KEYS_DURING_ACTION, TaskListBox,
    get_error_colors, FocusedTask, ExitMainLoop,
)


CLIENT_MODULE = 'just_start_urwid.client'


@fixture
def action_runner(mocker):
    pomodoro_timer = mocker.create_autospec(PomodoroTimer)
    return ActionRunner(pomodoro_timer, print, print)


@fixture
def focused_task(mocker):
    return mocker.create_autospec(TaskWidget)


@fixture
def action_handler(action_runner, focused_task):
    return ActionHandler(action_runner, focused_task)


@fixture
def action_handler_after_input(action_handler, request):
    default_action = Action.ADD
    default_text = 'default input'
    try:
        action_handler.action = request.param.get('action', default_action)
        action_handler.focused_task.edit_text = request.param.get('edit_text', default_text)
    except AttributeError:
        action_handler.action = default_action
        action_handler.focused_task.edit_text = default_text
    return action_handler


def assert_key_resets_action(key: str, action_handler_after_input):
    action_handler_after_input.handle_key_for_started_unary_action(key)
    assert action_handler_after_input.action is None


class TestActionHandler:
    def test_handle_key_for_action_raises_action_not_in_progress(self, action_handler):
        with raises(ActionNotInProgress):
            action_handler.handle_key_for_started_unary_action('')

    @mark.parametrize('key', NULLARY_ACTION_KEYS.keys())
    def test_start_nullary_action(self, key: str, action_handler):
        action_handler.start_action(key)

    @mark.parametrize('key', UNARY_ACTION_KEYS.keys())
    def test_start_unary_action(self, key: str, action_handler):
        action_handler.start_action(key)

    @mark.parametrize('action_handler_after_input',
                      [{'action': action} for action in UNARY_ACTION_PROMPTS], indirect=True)
    def test_run_unary_action(self, action_handler_after_input):
        assert_key_resets_action('enter', action_handler_after_input)

    @mark.parametrize('action_handler_after_input',
                      [{'action': create_autospec(Action.ADD)}], indirect=True)
    def test_cancel_action(self, action_handler_after_input):
        action_to_cancel = action_handler_after_input.action
        assert_key_resets_action('esc', action_handler_after_input)
        action_to_cancel.assert_not_called()

    @mark.parametrize('key', IGNORED_KEYS_DURING_ACTION)
    def test_ignored_keys(self, key: str, action_handler_after_input):
        action_handler_after_input.handle_key_for_started_unary_action(key)
        assert action_handler_after_input.action is not None

    def test_invalid_key(self, action_handler):
        with raises(UserInputError):
            action_handler.read_action_from_user('@')


@fixture
def focused_task(mocker):
    mock_task_list_box = mocker.create_autospec(TaskListBox)
    mock_task_list_box.focus = mocker.create_autospec(TaskWidget)
    return FocusedTask(mock_task_list_box)


class TestFocusedTask:
    def test_get_attr(self, focused_task):
        assert focused_task.task_id

    def test_set_attr(self, focused_task):
        focused_task.task_id = '10'
        assert focused_task.task_id == '10'


@fixture
def task_list_box(action_handler):
    task_list_box = TaskListBox()
    task_list_box.action_handler = action_handler
    return task_list_box


class TestTaskListBox:
    def test_quit(self, task_list_box):
        with raises(ExitMainLoop):
            task_list_box.keypress(0, 'q')

    @mark.parametrize('key', ['down', 'j'])
    def test_down_keys(self, key: str, task_list_box):
        self.assert_key_translates_to(key, 'down', task_list_box)

    @mark.parametrize('key', ['up', 'k'])
    def test_up_keys(self, key: str, task_list_box):
        self.assert_key_translates_to(key, 'up', task_list_box)

    def test_action_key(self, task_list_box):
        task_list_box.keypress(0, 'h')

    @staticmethod
    def assert_key_translates_to(key: str, translated_key: str, task_list_box):
        with patch(f'{CLIENT_MODULE}.ListBox.keypress', autospec=True) as spec:
            task_list_box.keypress(0, key)
            spec.assert_called_once_with(task_list_box, 0, translated_key)


@fixture
def task_widget():
    return TaskWidget('1 ignored_text')


class TestTaskWidget:
    def test_task_id(self, task_widget):
        self.assert_id('1', task_widget)

    def test_task_id_setter(self, task_widget):
        task_widget.task_id = '2'
        self.assert_id('2', task_widget)

    @staticmethod
    def assert_id(task_id: str, task_widget):
        assert task_widget.task_id == task_id


def test_get_error_colors():
    error_fg = 'fg'
    error_bg = 'bg'
    colors = get_error_colors(lambda _: {'error_fg': error_fg, 'error_bg': error_bg})
    assert colors == (error_fg, error_bg)
