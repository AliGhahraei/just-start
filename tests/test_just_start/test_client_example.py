from pytest import mark, fixture

from just_start import PromptSkippedPhases
from just_start.client_example import main as client_main, run_nullary_action
from just_start.constants import INVALID_ACTION_KEY, SKIP_NOT_ENABLED


@fixture
def main_sysout(mocker, capsys, request):
    keypresses = request.param['keypresses']
    side_effect = *keypresses, 'q'

    mocker.patch('just_start.client_example.prompt', side_effect=side_effect)
    for var in ('GREEN', 'BLUE', 'RED', 'RESTORE_COLOR'):
        mocker.patch(f'just_start.client_example.{var}', '')

    client_main()
    return capsys.readouterr()[1]


@fixture
def mock_action_runner(mocker):
    class _MockActionRunner:
        def __call__(self, *_, **__):
            raise PromptSkippedPhases()

        @mocker.create_autospec
        def skip_phases(self, phases: int):
            pass

    return _MockActionRunner()


def simulate_keypresses(*args):
    return ({'keypresses': keypresses} for keypresses in args)


@mark.parametrize('main_sysout', simulate_keypresses(
        ('a', 'Task description',),
        ('c', '1',),
        ('d', '1',),
        ('m', 'task data', '1',),
        ('!', 'task',),
        ('!', 'command',),
        ('h',),
        ('p',),
        ('p', 'p',),
        ('t',),
        ('y',),
), indirect=True)
def test_right_action(main_sysout):
    assert_no_sysout_errors_except(main_sysout)


@mark.parametrize('main_sysout', simulate_keypresses('s'), indirect=True)
def test_skip_not_enabled(main_sysout):
    assert_no_sysout_errors_except(main_sysout, SKIP_NOT_ENABLED)


def test_prompt_skipped_phases(mocker, mock_action_runner):
    phases = '3'
    with mocker.patch('just_start.client_example.prompt', side_effect=phases):
        run_nullary_action(mock_action_runner, 'fake_action')
        mock_action_runner.skip_phases.assert_called_once_with(mock_action_runner, phases=phases)


@mark.parametrize('main_sysout', simulate_keypresses('w'), indirect=True)
def test_wrong_action(main_sysout):
    assert_no_sysout_errors_except(main_sysout, f'{INVALID_ACTION_KEY} "w"')


def test_keyboard_interrupt(mocker, capsys):
    mocker.patch('just_start.client_example.prompt', raise_keyboard_interrupt)
    client_main()

    sysout = capsys.readouterr()[0]
    assert_no_sysout_errors_except(sysout)


def assert_no_sysout_errors_except(sysout, *expected_errors):
    actual_errors = {error for error in sysout.split('\n') if error}
    assert set(expected_errors) == actual_errors


def raise_keyboard_interrupt(*_, **__):
    raise KeyboardInterrupt
