from pytest import mark, fixture

from just_start.client_example import main as client_main
from just_start.constants import INVALID_ACTION_KEY


@fixture
def main_sysout(mocker, capsys, request):
    keypresses = request.param['keypresses']
    side_effect = *keypresses, 'q'

    mocker.patch('just_start.client_example.prompt', side_effect=side_effect)
    for var in ('GREEN', 'BLUE', 'RED', 'RESTORE_COLOR'):
        mocker.patch(f'just_start.client_example.{var}', '')

    client_main()
    return capsys.readouterr()[1]


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
        ('s',),
        ('y',),
), indirect=True)
def test_right_action(main_sysout):
    assert_no_sysout_errors_except(main_sysout)


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
