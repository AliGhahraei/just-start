#!/usr/bin/env python3
import shelve
from datetime import datetime, timedelta
from enum import Enum
from functools import partial
from itertools import cycle
from pickle import HIGHEST_PROTOCOL
from platform import system
from subprocess import run
from threading import Timer
from typing import Callable, Dict, Any, Tuple

from just_start.constants import PERSISTENT_PATH
from just_start.config_reader import config
from just_start.utils import JustStartError


STOP_MESSAGE = 'Pomodoro timer stopped'


def time_after_seconds(seconds_left: int) -> str:
    end_time = datetime.now() + timedelta(seconds=seconds_left)
    return end_time.strftime('%H:%M')


class Phase(Enum):
    WORK = 'Work and switch tasks'
    SHORT_REST = 'Short break'
    LONG_REST = 'LONG BREAK!!!'


class PomodoroError(JustStartError):
    pass


class PomodoroTimer:
    SERIALIZABLE_ATTRIBUTES = ('pomodoro_cycle', 'phase', 'time_left',
                               '_at_work_override')

    def __init__(self, status_callback: Callable[[str], None],
                 blocking_callback: Callable[[bool], None],
                 at_work_override: bool=False, notify: bool=False):
        self.status_callback = status_callback
        self.blocking_callback = blocking_callback

        self._at_work_override = at_work_override
        self.location = 'work' if self.at_work else 'home'

        self.start_datetime = self.timer = None
        self.is_running = False
        self.work_count = 0
        self.PHASE_DURATION = self._generate_phase_duration()

        self.pomodoro_cycle = self._create_cycle()
        self.phase, self.time_left = self._get_next_phase_and_time_left()

        if notify:
            self.notify(STOP_MESSAGE)

    @property
    def serializable_data(self) -> Dict[str, Any]:
        self._pause()
        return {attribute: self.__getattribute__(attribute) for attribute
                in self.SERIALIZABLE_ATTRIBUTES}

    @serializable_data.setter
    def serializable_data(self, data: Dict) -> None:
        for attribute, value in data.items():
            self.__setattr__(attribute, value)

    def _pause(self) -> None:
        self._cancel_timer()
        self.is_running = False
        self.blocking_callback(True)

    def _cancel_timer(self) -> None:
        if self.is_running:
            self.timer.cancel()
            elapsed_timedelta = datetime.now() - self.start_datetime
            self.time_left -= elapsed_timedelta.seconds

    @property
    def at_work(self) -> bool:
        if self._at_work_override:
            return True

        return datetime.now().isoweekday() < 6 and (
                config['work']['start']
                <= datetime.now().time()
                <= config['work']['end'])

    @property
    def skip_enabled(self) -> bool:
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
            try:
                return db['skip_enabled']
            except KeyError:
                db['skip_enabled'] = False
                return False

    def _generate_phase_duration(self) -> Dict:
        location_config = config[self.location]

        durations = (duration * 60 for duration in (
            location_config['pomodoro_length'], location_config['short_rest'],
            location_config['long_rest']))
        # noinspection PyTypeChecker
        phase_duration = dict(zip(Phase, durations))
        return phase_duration

    def _create_cycle(self) -> cycle:
        states = ([Phase.WORK, Phase.SHORT_REST]
                  * config[self.location]['cycles_before_long_rest'])
        states[-1] = Phase.LONG_REST
        return cycle(states)

    def _get_next_phase_and_time_left(self) -> Tuple[Phase, int]:
        next_phase = next(self.pomodoro_cycle)
        return next_phase, self.PHASE_DURATION[next_phase]

    def notify(self, status: str) -> None:
        if system() == 'Linux':
            run(['notify-send', status])
        else:
            # noinspection SpellCheckingInspection
            run(['osascript', '-e', f'display notification "{status}" with'
                                    f' title "just-start"'])

        self.status_callback(status)

    def toggle(self) -> None:
        if self.is_running:
            self._pause()
            self.notify('Paused')
        else:
            self._run()

    def _run(self) -> None:
        self.start_datetime = datetime.now()
        now = self.start_datetime.time().strftime('%H:%M')
        pomodoros = 'pomodoro' if self.work_count == 1 else 'pomodoros'
        self.notify(f'{self.phase.value} - {self.work_count} {pomodoros} so'
                    f' far at {"work" if self.at_work else "home"}.'
                    f'\n{now} - {time_after_seconds(self.time_left)}'
                    f' ({int(self.time_left / 60)} mins)')

        self.timer = Timer(self.time_left, partial(self.advance_phases, False))
        self.timer.start()
        self.is_running = True
        self.blocking_callback(self.phase is self.phase.WORK)

    def advance_phases(self, is_skipping: bool=True,
                       phases_skipped: int=1) -> None:
        if is_skipping and self.phase is self.phase.WORK:
            with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db:
                db['skip_enabled'] = False

        self._cancel_timer()

        if self.phase is self.phase.WORK:
            self.work_count += 1

        # Skipped work phases count as finished, except for the current one
        for _ in range(phases_skipped - 1):
            self.phase, self.time_left = self._get_next_phase_and_time_left()

            if self.phase is self.phase.WORK:
                self.work_count += 1

        self.phase, self.time_left = self._get_next_phase_and_time_left()
        self._run()

    def reset(self, at_work_override: bool) -> None:
        self._pause()
        self.__init__(self.status_callback,
                      self.blocking_callback,
                      at_work_override=at_work_override,
                      notify=True)
