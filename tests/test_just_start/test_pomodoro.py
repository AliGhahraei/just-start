from datetime import datetime, timedelta

from pytest import mark, fixture, raises

from just_start.os_utils import UserInputError
from just_start.pomodoro import time_after_seconds, PomodoroTimer, PromptSkippedPhases


@mark.parametrize('seconds_left', [0, 1, 10])
def test_time_after_seconds(seconds_left):
    expected_time = datetime.now() + timedelta(seconds=seconds_left)
    assert time_after_seconds(seconds_left) == expected_time.strftime('%H:%M')


@fixture
def pomodoro_timer(mocker):
    timer = PomodoroTimer(print)
    with mocker.patch('just_start.pomodoro.db'):
        try:
            yield timer
        finally:
            timer.reset()


@fixture
def skip_enabled_pomodoro_timer(mocker):
    timer = PomodoroTimer(print)
    with mocker.patch('just_start.pomodoro.db'):
        timer.skip_enabled = True
        try:
            yield timer
        finally:
            timer.reset()


class TestPomodoroTimer:
    def test_advance_phases_when_allowed(self, skip_enabled_pomodoro_timer):
        skip_enabled_pomodoro_timer.advance_phases(phases_skipped=2)

    def test_advance_invalid_number_of_phases(self, skip_enabled_pomodoro_timer):
        with raises(UserInputError):
            skip_enabled_pomodoro_timer.advance_phases(phases_skipped=0)

    def test_skipped_phases_prompt(self, skip_enabled_pomodoro_timer):
        with raises(PromptSkippedPhases):
            skip_enabled_pomodoro_timer.advance_phases(phases_skipped=None)

    def test_advance_phases(self, skip_enabled_pomodoro_timer):
        skip_enabled_pomodoro_timer.advance_phases(is_skipping=False, phases_skipped=2)
