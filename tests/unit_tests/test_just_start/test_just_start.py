import just_start.constants as const
# noinspection PyProtectedMember
from just_start._just_start import _handle_errors


def test_unhandled_error_message(capsys):
    ex = Exception()
    with _handle_errors():
        raise ex

    assert const.UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH in capsys.readouterr()[1]
