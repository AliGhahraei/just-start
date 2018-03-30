from datetime import datetime, timedelta

from pytest import mark

from just_start.pomodoro.pomodoro import time_after_seconds


@mark.parametrize('seconds_left', [0, 1, 10, 10000000])
def test_time_after_seconds(seconds_left):
    expected_time = datetime.now() + timedelta(seconds=seconds_left)
    assert time_after_seconds(seconds_left) == expected_time.strftime('%H:%M')
