#!/usr/bin/env python3
import shelve
from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
from pickle import HIGHEST_PROTOCOL
from platform import system
from subprocess import run
from threading import Timer
from typing import Callable, Dict, Optional, Any

from just_start.constants import PERSISTENT_PATH
from just_start.config_reader import config
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
    SERIALIZABLE_ATTRIBUTES = ('pomodoro_cycle', 'state', 'time_left',
                               'at_work_user_overridden')

    def __init__(self, external_status_function: Callable[[str], None],
                 external_blocking_function: Callable[[bool], None],
                 at_work_user_overridden: Optional[bool]=None,
                 notify: bool=False, pomodoro_cycle=None, state=None,
                 time_left=None):
        self.external_status_function = external_status_function
        self.external_blocking_function = external_blocking_function

        self.at_work_user_overridden = at_work_user_overridden
        self.location = 'work' if self.user_is_at_work() else 'home'

        self.start_datetime = self.timer = None
        self.is_running = False
        self.work_count = 0
        self.PHASE_DURATION = self._generate_phase_duration()

        if pomodoro_cycle and state and time_left:
            self.pomodoro_cycle = pomodoro_cycle
            self.state = state
            self.time_left = time_left
        else:
            self.pomodoro_cycle = self._create_cycle()
            self._update_state_and_time_left()

        if notify:
            self.notify(STOP_MESSAGE)

    @property
    def serializable_data(self) -> Dict[str, Any]:
        self._pause()
        return {attribute: self.__getattribute__(attribute) for attribute
                in self.SERIALIZABLE_ATTRIBUTES}

    def _pause(self) -> None:
        if self.is_running:
            self.timer.cancel()
            elapsed_timedelta = datetime.now() - self.start_datetime
            self.time_left -= elapsed_timedelta.seconds

    def user_is_at_work(self) -> bool:
        if self.at_work_user_overridden is not None:
            return self.at_work_user_overridden

        return datetime.now().isoweekday() < 6 and (
                config['work']['start']
                <= datetime.now().time()
                <= config['work']['end'])

    def _generate_phase_duration(self) -> Dict:
        location_config = config[self.location]

        durations = (duration * 60 for duration in (
            location_config['pomodoro_length'], location_config['short_rest'],
            location_config['long_rest']))
        # noinspection PyTypeChecker
        phase_duration = dict(zip(Phases, durations))
        return phase_duration

    def _create_cycle(self) -> cycle:
        states = ([Phases.WORK, Phases.SHORT_REST]
                  * config[self.location]['cycles_before_long_rest'])
        states[-1] = Phases.LONG_REST
        return cycle(states)

    def _update_state_and_time_left(self) -> None:
        self.state = next(self.pomodoro_cycle)
        self.time_left = self.PHASE_DURATION[self.state]

    def notify(self, status: str) -> None:
        if system() == 'Linux':
            run(['notify-send', status])
        else:
            # noinspection SpellCheckingInspection
            run(['osascript', '-e',
                 f'display notification "{status}" with title'
                 f' "just-start"'])

        self.external_status_function(status)

    def toggle(self) -> None:
        if self.is_running:
            self._pause()
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

        self._pause()
        self.is_running = True

        for _ in range(phases_skipped):
            self._update_state_and_time_left()
        self._run()

        self.external_blocking_function(self.state is self.state.WORK)

    def reset(self, at_work_user_overridden: Optional[bool]=None) -> None:
        self._pause()
        self.__init__(self.external_status_function,
                      self.external_blocking_function,
                      at_work_user_overridden=at_work_user_overridden,
                      notify=True)
        self.external_blocking_function(True)
