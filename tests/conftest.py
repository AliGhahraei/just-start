from unittest.mock import patch
from subprocess import CompletedProcess

from pytest import fixture


def raise_keyboard_interrupt(*_, **__):
    raise KeyboardInterrupt


@fixture(scope='session', autouse=True)
def mock_os_commands():
    def run_mock(*args, **__):
        return CompletedProcess(args, stdout=b'', returncode=0)

    with patch('just_start.os_utils.run', run_mock), \
            patch('just_start.os_utils.spawn', autospec=True):
        yield
