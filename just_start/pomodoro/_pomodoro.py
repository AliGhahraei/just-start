#!/usr/bin/env python3
import shelve
from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
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
        self.state, self.POMODORO_CYCLE = self.get_state_and_cycle()
        self.external_blocking_function = external_blocking_function
        self.work_count = 0
        self._update_state()
        self.is_running = False
        self.start_datetime = self.timer = None
        self.notify(STOP_MESSAGE,
                    desktop_stop_notification=show_external_stop_notification)

    def get_state_and_cycle(self) -> Tuple[Enum, cycle]:
        location = 'work' if self.user_is_at_work() else 'home'
        location_config = self.config[location]

        work_time = location_config['pomodoro_length']
        short_rest_time = location_config['short_rest']
        long_rest_time = location_config['long_rest']
        cycles_before_long_rest = location_config['cycles_before_long_rest']

        # noinspection PyArgumentList
        state_enum = Enum('state', [
            ('WORK', ('SWITCH! (and work)', work_time * 60)),
            ('SHORT_REST', ('Short rest', short_rest_time * 60)),
            ('LONG_REST', ('LONG REST!!!', long_rest_time * 60))
        ])

        states = ([state_enum.WORK, state_enum.SHORT_REST]
                  * cycles_before_long_rest)
        states[-1] = state_enum.LONG_REST

        return state_enum, cycle(states)

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
        self.notify(f'{self.state.value[0]} ({self.work_count} pomodoros so'
                    f' far). End time: {time_after_seconds(self.time_left)}'
                    f' ({int(self.time_left / 60)} mins). You are at'
                    f' {"work" if self.user_is_at_work() else "home"}')

        self.timer = Timer(self.time_left,
                           self._timer_triggered_phase_advancement)
        self.timer.start()

    def _update_state(self) -> None:
        self.state = self.POMODORO_CYCLE.__next__()
        self.time_left = self.state.value[1]

    def _timer_triggered_phase_advancement(self) -> None:
        self.advance_phases(timer_triggered=True)

    def advance_phases(self, timer_triggered: bool=False,
                       phases_skipped: int=1) -> None:
        if self.state is self.state.WORK:
            with shelve.open(PERSISTENT_PATH) as db:
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
