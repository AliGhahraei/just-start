from subprocess import CompletedProcess
from unittest.mock import patch

from pytest import fixture

from just_start.logging import file_handler, logger


@fixture(scope='session', autouse=True)
def remove_file_handler_from_log():
    logger.removeHandler(file_handler)


@fixture(scope='session', autouse=True)
def mock_os_commands():
    def run_mock(*args, **__):
        return CompletedProcess(args, stdout=b'', returncode=0)

    with patch('just_start.os_utils.run', run_mock), \
            patch('just_start.os_utils.spawn', autospec=True):
        yield
