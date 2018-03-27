#!/usr/bin/env python3
import shelve
from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
from pickle import HIGHEST_PROTOCOL
from platform import system
from subprocess import run
from threading import Timer
from types import TracebackType
from typing import Callable, Dict, Optional, Tuple

from just_start.constants import PERSISTENT_PATH
from .constants import STOP_MESSAGE


def time_after_seconds(seconds_left: int) -> str:
    end_time = datetime.now() + timedelta(seconds=seconds_left)
    return end_time.strftime('%H:%M')


class Phases(Enum):
    WORK = 'Work and switch tasks'
    SHORT_REST = 'Short break'
    LONG_REST = 'LONG BREAK!!!'


class PomodoroError(Exception):
    pass


class PomodoroTimer:
    def __init__(self, external_status_function: Callable[[str], None],
                 external_blocking_function: Callable[[bool], None],
                 config: Dict, at_work_user_overridden: Optional[bool]=None,
                 show_external_stop_notification: bool=False):
        self.config = config
        self.external_status_function = external_status_function
        self.at_work_user_overridden = at_work_user_overridden
        self.PHASE_DURATION, self.POMODORO_CYCLE = self.get_duration_and_cycle()
        self.external_blocking_function = external_blocking_function
        self.work_count = 0
        self._update_state()
        self.is_running = False
        self.start_datetime = self.timer = None
        self.notify(STOP_MESSAGE,
                    desktop_stop_notification=show_external_stop_notification)

    def get_duration_and_cycle(self) -> Tuple[Dict, cycle]:
        location = 'work' if self.user_is_at_work() else 'home'
        location_config = self.config[location]

        durations = (duration * 60 for duration in (
            location_config['pomodoro_length'], location_config['short_rest'],
            location_config['long_rest']))
        # noinspection PyTypeChecker
        phase_duration = dict(zip(Phases, durations))

        cycles_before_long_rest = location_config['cycles_before_long_rest']
        states = [Phases.WORK, Phases.SHORT_REST] * cycles_before_long_rest
        states[-1] = Phases.LONG_REST

        return phase_duration, cycle(states)

    def notify(self, status: str, desktop_stop_notification: bool=True) -> None:
        if desktop_stop_notification:
            if system() == 'Linux':
                run(['notify-send', status])
            else:
                # noinspection SpellCheckingInspection
                run(['osascript', '-e',
                     f'display notification "{status}" with title'
                     f' "just-start"'])

        self.external_status_function(status)

    def user_is_at_work(self) -> bool:
        if self.at_work_user_overridden is not None:
            return self.at_work_user_overridden

        return datetime.now().isoweekday() < 6 and (
                self.config['work']['start']
                <= datetime.now().time()
                <= self.config['work']['end'])

    def toggle(self) -> None:
        if self.is_running:
            self.timer.cancel()

            elapsed_timedelta = datetime.now() - self.start_datetime
            self.time_left -= elapsed_timedelta.seconds

            self.notify('Paused')
            self.external_blocking_function(True)
        else:
            self._run()
            self.external_blocking_function(self.state is self.state.WORK)

        self.is_running = not self.is_running

    def _run(self) -> None:
        self.start_datetime = datetime.now()
        now = self.start_datetime.time().strftime('%H:%M')
        self.notify(f'{self.state.value} - {self.work_count} pomodoros so'
                    f' far at {"work" if self.user_is_at_work() else "home"}.'
                    f'\n{now} - {time_after_seconds(self.time_left)}'
                    f' ({int(self.time_left / 60)} mins)')

        self.timer = Timer(self.time_left,
                           self._timer_triggered_phase_advancement)
        self.timer.start()

    def _update_state(self) -> None:
        self.state = next(self.POMODORO_CYCLE)
        self.time_left = self.PHASE_DURATION[self.state]

    def _timer_triggered_phase_advancement(self) -> None:
        self.advance_phases(timer_triggered=True)

    def advance_phases(self, timer_triggered: bool=False,
                       phases_skipped: int=1) -> None:
        if self.state is self.state.WORK:
            with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
                try:
                    skip_enabled = db['skip_enabled']
                except KeyError:
                    db['skip_enabled'] = skip_enabled = False

                if not timer_triggered and not skip_enabled:
                    raise PomodoroError('Sorry, please work 1 pomodoro to'
                                        ' re-enable work skipping')

                self.work_count += 1
                db['skip_enabled'] = timer_triggered
        elif phases_skipped > 1:
            raise PomodoroError("Sorry, you can't skip more than 1 phase"
                                " while not working")

        self._stop_countdown()
        self.is_running = True

        for _ in range(phases_skipped):
            self._update_state()
        self._run()

        self.external_blocking_function(self.state is self.state.WORK)

    def reset(self, at_work_user_overridden: Optional[bool]=None) -> None:
        self._stop_countdown()
        self.__init__(self.external_status_function,
                      self.external_blocking_function, self.config,
                      at_work_user_overridden=at_work_user_overridden,
                      show_external_stop_notification=True)
        self.external_blocking_function(True)

    def __enter__(self) -> 'PomodoroTimer':
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Exception],
                 traceback: Optional[TracebackType]) -> None:
        self._stop_countdown()
        self.external_blocking_function(True)

    def _stop_countdown(self) -> None:
        if self.is_running:
            self.timer.cancel()
