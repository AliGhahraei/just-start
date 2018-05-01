from subprocess import CompletedProcess
from unittest.mock import patch

from pytest import fixture

from just_start._just_start import create_module_vars


def raise_keyboard_interrupt(*_, **__):
    raise KeyboardInterrupt


@fixture(scope='session', autouse=True)
def mock_os_commands():
    def run_mock(*args, **__):
        return CompletedProcess(args, stdout=b'', returncode=0)

    with patch('just_start.os_utils.run', run_mock), \
            patch('just_start.os_utils.spawn', autospec=True):
        yield


@fixture
def recreate_just_start_module_vars(mocker):
    module_vars = create_module_vars()
    module_var_names = 'status_manager', 'pomodoro_timer'
    assert len(module_vars) == len(module_var_names)

    for var, name in zip(module_vars, module_var_names):
        mocker.patch(f'just_start._just_start.{name}', var)
