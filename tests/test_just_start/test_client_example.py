from contextlib import contextmanager
from pytest import mark, fixture

from just_start import log
from just_start.client_example import main as client_main
from just_start.constants import (
    INVALID_ACTION_KEY, SKIP_NOT_ENABLED, SKIP_ENABLED, POSSIBLE_ERRORS
)


@fixture
def main_sysout(mocker, capsys, request):
    try:
        keypresses = request.param['keypresses']
    except KeyError:
        side_effect = request.param['side_effect']
    else:
        side_effect = *keypresses, 'q'

    db_data = request.param.get('db', {})
    log.debug(db_data)

    @contextmanager
    def db_mock(*_, **__):
        yield db_data

    mocker.patch('just_start.os_utils.shelve.open', db_mock)
    mocker.patch('just_start.client_example.prompt', side_effect=side_effect)

    client_main()
    return capsys.readouterr()[0]


def simulate_keypresses(*args):
    return ({'keypresses': keypresses} for keypresses in args)


@mark.parametrize('main_sysout', simulate_keypresses(
        ('a', 'Task description',),
        ('c', '1',),
        ('d', '1',),
        ('m', 'task data', '1',),
        ('!', 'task',),
        ('l', 'w',),
        ('l', 'h',),
        ('!', 'command',),
        ('h',),
        ('p',),
        ('p', 'p',),
        ('t',),
        ('y',),
), indirect=True)
def test_right_action(main_sysout):
    assert_no_sysout_errors_except(main_sysout)


@mark.parametrize('main_sysout', (({'keypresses': ('s', '1'),
                                    'db': {SKIP_ENABLED: True}}),),
                  indirect=True)
def test_skip_enabled(main_sysout):
    assert_no_sysout_errors_except(main_sysout)


@mark.parametrize('main_sysout', simulate_keypresses('s'), indirect=True)
def test_skip_not_enabled(main_sysout):
    assert_no_sysout_errors_except(main_sysout, SKIP_NOT_ENABLED)


@mark.parametrize('main_sysout', simulate_keypresses('w', 'x'), indirect=True)
def test_wrong_action(main_sysout):
    assert_no_sysout_errors_except(main_sysout, INVALID_ACTION_KEY)


def test_keyboard_interrupt(mocker, capsys):
    mocker.patch('just_start.client_example.prompt', raise_keyboard_interrupt)
    client_main()

    sysout = capsys.readouterr()[0]
    assert_no_sysout_errors_except(sysout)


def assert_no_sysout_errors_except(sysout, *allowed_errors):
    for error in allowed_errors:
        assert error in sysout

    assert not (set(allowed_errors) - POSSIBLE_ERRORS)


def raise_keyboard_interrupt(*_, **__):
    raise KeyboardInterrupt
