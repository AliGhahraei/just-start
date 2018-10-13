from unittest.mock import create_autospec
from pytest import fixture, raises, mark

from just_start import Action, UNARY_ACTIONS, NULLARY_ACTION_KEYS, UNARY_ACTION_KEYS
from just_start_urwid.client import (
    ActionRunner, ActionNotInProgress, TaskWidget, IGNORED_KEYS_DURING_ACTION
)


@fixture
def action_runner(mocker):
    focused_task = mocker.create_autospec(TaskWidget)
    return ActionRunner(focused_task)


@fixture
def action_runner_after_input(action_runner, request):
    default_action = Action.ADD
    default_text = 'default input'
    try:
        action_runner.action = request.param.get('action', default_action)
        action_runner.focused_task.edit_text = request.param.get('edit_text', default_text)
    except AttributeError:
        action_runner.action = default_action
        action_runner.focused_task.edit_text = default_text
    return action_runner


def assert_key_resets_action(key: str, action_runner_after_input):
    action_runner_after_input.handle_key_for_action(key)
    assert action_runner_after_input.action is None


class TestActionRunner:
    def test_handle_key_for_action_raises_action_not_in_progress(self, action_runner):
        with raises(ActionNotInProgress):
            action_runner.handle_key_for_action('')

    @mark.parametrize('key', NULLARY_ACTION_KEYS.keys())
    def test_start_nullary_action(self, key: str, action_runner):
        action_runner.start_action(key)

    @mark.parametrize('key', UNARY_ACTION_KEYS.keys())
    def test_start_unary_action(self, key: str, action_runner):
        action_runner.start_action(key)

    @mark.parametrize('action_runner_after_input',
                      [{'action': action} for action in UNARY_ACTIONS], indirect=True)
    def test_run_unary_action(self, action_runner_after_input):
        assert_key_resets_action('enter', action_runner_after_input)

    @mark.parametrize('action_runner_after_input',
                      [{'action': create_autospec(Action.ADD)}], indirect=True)
    def test_cancel_action(self, action_runner_after_input):
        action_to_cancel = action_runner_after_input.action
        assert_key_resets_action('esc', action_runner_after_input)
        action_to_cancel.assert_not_called()

    @mark.parametrize('key', IGNORED_KEYS_DURING_ACTION)
    def test_ignored_keys(self, key: str, action_runner_after_input):
        action_runner_after_input.handle_key_for_action(key)
        assert action_runner_after_input.action is not None
