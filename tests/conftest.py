from pytest import fixture
from unittest.mock import patch, MagicMock


@fixture(scope='session', autouse=True)
def mock_subprocess_run():
    class RunMock(MagicMock):
        returncode = 0

    with patch('just_start.utils.run', lambda *_, **__: RunMock()), \
            patch('just_start.pomodoro.run', lambda *_, **__: RunMock()):
        yield
