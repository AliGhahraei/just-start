from pytest import fixture, raises, mark

from just_start import Action, UNARY_ACTIONS
from just_start_urwid.client import (
    ActionRunner, ActionNotInProgress, TaskWidget
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


class TestActionRunner:
    def test_handle_key_for_action_raises_action_not_in_progress(self, action_runner):
        with raises(ActionNotInProgress):
            action_runner.handle_key_for_action('')

    @mark.parametrize('action_runner_after_input',
                      [{'action': action} for action in UNARY_ACTIONS], indirect=True)
    def test_handle_enter(self, action_runner_after_input):
        action_runner_after_input.handle_key_for_action('enter')
