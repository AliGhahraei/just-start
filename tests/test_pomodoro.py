import atexit
from datetime import datetime, timedelta

from pytest import mark, fixture

from just_start import quit_gracefully
from just_start.pomodoro import time_after_seconds


@fixture(scope='session', autouse=True)
def unregister_quit():
    atexit.unregister(quit_gracefully)


@mark.parametrize('seconds_left', [0, 1, 10, 10000000])
def test_time_after_seconds(seconds_left):
    expected_time = datetime.now() + timedelta(seconds=seconds_left)
    assert time_after_seconds(seconds_left) == expected_time.strftime('%H:%M')
