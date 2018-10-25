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


class TestPomodoroTimer:
    def test_advance_phases(self, pomodoro_timer):
        pomodoro_timer.advance_phase()
