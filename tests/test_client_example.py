from pytest import mark, fixture

from just_start.client_example import main as client_main
from just_start.constants import INVALID_ACTION_KEY


@fixture
def main_sysout(mocker, capsys, request):
    user_input = (*request.param, 'q')
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
    ('s', '1',),
    ('r',),
    ('t',),
    ('y',),
), indirect=True)
def test_right_action(main_sysout):
    assert INVALID_ACTION_KEY not in main_sysout


@mark.parametrize('main_sysout', (
    ('w',),
    ('x',),
), indirect=True)
def test_wrong_action(main_sysout):
    assert INVALID_ACTION_KEY in main_sysout


def test_keyboard_interrupt(mocker):
    def raise_keyboard_interrupt(*_, **__):
        raise KeyboardInterrupt

    mocker.patch('just_start.client_example.prompt', raise_keyboard_interrupt)
    client_main()
