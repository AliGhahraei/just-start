from pytest import fixture

from just_start.pomodoro import PomodoroTimer


@fixture
def pomodoro_timer():
    timer = PomodoroTimer(print)
    try:
        yield timer
    finally:
        timer.reset()


class TestPomodoroTimer:
    pass
