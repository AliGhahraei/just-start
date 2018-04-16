from contextlib import contextmanager
from pytest import mark, fixture

from just_start.client_example import main as client_main
from just_start.constants import (
    INVALID_ACTION_KEY, SKIP_NOT_ENABLED, INVALID_PHASE_NUMBER
)


@fixture(autouse=True)
def mock_db(mocker):
    db = {}

    @contextmanager
    def db_mock():
        yield db

    mocker.patch('just_start.os_utils._db', db_mock)


@fixture
def main_sysout(mocker, capsys, request):
    user_input = *request.param, 'q'
    mocker.patch('just_start.client_example.prompt', side_effect=user_input)
    client_main()
    return capsys.readouterr()[0]


@mark.parametrize('main_sysout', (
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


@mark.parametrize('main_sysout', (('s',),), indirect=True)
def test_skip_not_allowed(main_sysout):
    assert SKIP_NOT_ENABLED in main_sysout


@mark.parametrize('main_sysout', (('w',), ('x',),), indirect=True)
def test_wrong_action(main_sysout):
    assert INVALID_ACTION_KEY in main_sysout


def test_keyboard_interrupt(mocker):
    def raise_keyboard_interrupt(*_, **__):
        raise KeyboardInterrupt

    mocker.patch('just_start.client_example.prompt', raise_keyboard_interrupt)
    client_main()
