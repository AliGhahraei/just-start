from pytest import fixture

from just_start.client_example import main
from just_start.constants import INVALID_ACTION_KEY


@fixture
def user_mock(mocker):
    def prompt_mock(*args):
        mocker.patch('just_start.client_example.prompt',
                     side_effect=[*args, 'q'])
    return prompt_mock


# noinspection PyShadowingNames
def test_right_actions(user_mock, capsys):
    user_mock(
        'a', 'Task description',
        'c', '1',
        'd', '1',
        'm', 'task data', '1',
        '!', 'task',
        'l', 'w',
        'l', 'h',
        '!', 'command',
        'h',
        'p',
        'p',
        's',
        'r',
        't',
        'y',
    )
    main()
    out, _ = capsys.readouterr()
    assert INVALID_ACTION_KEY not in out


# noinspection PyShadowingNames
def test_wrong_key(user_mock, capsys):
    user_mock('z')
    main()
    out, _ = capsys.readouterr()
    assert INVALID_ACTION_KEY in out
