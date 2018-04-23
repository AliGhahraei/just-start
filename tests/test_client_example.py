from contextlib import contextmanager
from pytest import mark, fixture

from conftest import raise_keyboard_interrupt
from just_start import log
from just_start.client_example import main as client_main
from just_start.constants import (
    INVALID_ACTION_KEY, SKIP_NOT_ENABLED, INVALID_PHASE_NUMBER, SKIP_ENABLED,
)


pytestmark = mark.usefixtures("recreate_just_start_module_vars")


@fixture
def main_sysout(mocker, capsys, request):
    db_data = request.param.get('db', {})
    log.debug(db_data)

    @contextmanager
    def db_mock(*_, **__):
        yield db_data

    mocker.patch('just_start.os_utils.shelve.open', db_mock)

    user_input = *request.param['input'], 'q'
    mocker.patch('just_start.client_example.prompt', side_effect=user_input)
    client_main()
    return capsys.readouterr()[0]


def input_param(*args):
    return ({'input': input_} for input_ in args)


@mark.parametrize('main_sysout', input_param(
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
        ('s',),
        ('t',),
        ('y',),
), indirect=True)
def test_right_action(main_sysout):
    assert INVALID_ACTION_KEY not in main_sysout


@mark.parametrize('main_sysout', (({'input': ('s', '1'),
                                    'db': {SKIP_ENABLED: True}}),),
                  indirect=True)
def test_skip_allowed(main_sysout):
    assert SKIP_NOT_ENABLED not in main_sysout


@mark.parametrize('main_sysout', input_param('s'), indirect=True)
def test_skip_not_allowed(main_sysout):
    assert SKIP_NOT_ENABLED in main_sysout


@mark.parametrize('main_sysout', input_param('w', 'x'), indirect=True)
def test_wrong_action(main_sysout):
    assert INVALID_ACTION_KEY in main_sysout


def test_keyboard_interrupt(mocker):
    mocker.patch('just_start.client_example.prompt', raise_keyboard_interrupt)
    client_main()
