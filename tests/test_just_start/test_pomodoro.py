from datetime import datetime, timedelta

from pytest import mark, fixture

from just_start.pomodoro import time_after_seconds, PomodoroTimer


@mark.parametrize('seconds_left', [0, 1, 10])
def test_time_after_seconds(seconds_left):
    expected_time = datetime.now() + timedelta(seconds=seconds_left)
    assert time_after_seconds(seconds_left) == expected_time.strftime('%H:%M')


@fixture
def pomodoro_timer():
    timer = PomodoroTimer(print)
    try:
        yield timer
    finally:
        timer.reset()


@fixture
def skip_enabled_pomodoro_timer(pomodoro_timer):
    pomodoro_timer.skip_enabled = True
    return pomodoro_timer


class TestPomodoroTimer:
    def test_advance_phases(self, skip_enabled_pomodoro_timer):
        skip_enabled_pomodoro_timer.advance_phase()
