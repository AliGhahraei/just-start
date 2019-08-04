#!/usr/bin/env python3
from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
from logging import getLogger
from typing import Dict, Any, Tuple, Callable, Iterator, Optional, Mapping

from just_start.constants import STOP_MESSAGE
from just_start.config_reader import get_location_name, get_pomodoro_config
from just_start.os_utils import block_sites


logger = getLogger(__name__)


StatusWriter = Callable[[str], None]


class PomodoroPhase(Enum):
    WORK = 'Work and switch tasks'
    SHORT_REST = 'Short break'
    LONG_REST = 'LONG BREAK!!!'


def _generate_phase_duration() -> Dict[PomodoroPhase, int]:
    pomodoro_config = get_pomodoro_config()
    durations = (duration * 60 for duration in (pomodoro_config.pomodoro_length,
                                                pomodoro_config.short_rest,
                                                pomodoro_config.long_rest))
    # noinspection PyTypeChecker
    phase_duration = dict(zip(PomodoroPhase, durations))
    return phase_duration


def _create_cycle() -> Iterator[PomodoroPhase]:
    states = ([PomodoroPhase.WORK, PomodoroPhase.SHORT_REST] *
              get_pomodoro_config().cycles_before_long_rest)
    states[-1] = PomodoroPhase.LONG_REST
    return cycle(states)


class PomodoroTimer:
    def __init__(self, notifier: StatusWriter, timer):
        self.start_datetime = None  # type: Optional[datetime]
        self.timer = timer
        self.is_running = False
        self.work_count = 0
        self.phase_duration = _generate_phase_duration()

        self.pomodoro_cycle = _create_cycle()
        self.pomodoro_phase, self.seconds_left = self._get_next_phase_and_seconds_left()
        self.notifier = notifier

    def _get_next_phase_and_seconds_left(self) -> Tuple[PomodoroPhase, int]:
        next_phase = next(self.pomodoro_cycle)
        return next_phase, self.phase_duration[next_phase]

    def toggle(self) -> None:
        if self.is_running:
            self._pause()
            self.notifier('Paused')
        else:
            self._run()

    def reset(self) -> None:
        self.stop()
        self.notifier(STOP_MESSAGE)
        self.__init__(notifier=self.notifier, timer=self.timer)  # type: ignore

    def stop(self):
        self._pause()

    def _pause(self) -> None:
        self._cancel_internal_timer()
        self.is_running = False
        block_sites(True)

    def _cancel_internal_timer(self) -> None:
        if self.is_running:
            self.timer.stop()
            assert self.start_datetime is not None
            elapsed_timedelta = datetime.now() - self.start_datetime
            self.seconds_left -= elapsed_timedelta.seconds

    def _run(self) -> None:
        self.start_datetime = datetime.now()
        now = self.start_datetime.time().strftime('%H:%M')
        pomodoros = 'pomodoro' if self.work_count == 1 else 'pomodoros'
        self.notifier(f'{self.pomodoro_phase.value} - {self.work_count} {pomodoros} so'
                      f' far at {get_location_name()}.'
                      f'\n{now} - {_add_to_time(self.start_datetime, self.seconds_left)}'
                      f' ({int(self.seconds_left / 60)} mins)')

        self.timer.start(self.seconds_left, self._advance_phase)
        self.is_running = True
        block_sites(self.pomodoro_phase is self.pomodoro_phase.WORK)

    def _advance_phase(self) -> None:
        self.work_count += 1
        self._cancel_internal_timer()

        self.pomodoro_phase, self.seconds_left = self._get_next_phase_and_seconds_left()
        self._run()


def _add_to_time(time: datetime, seconds_left: int) -> str:
    return (time + timedelta(seconds=seconds_left)).strftime('%H:%M')


class PomodoroSerializer:
    serializable_attributes = ('pomodoro_cycle', 'pomodoro_phase', 'seconds_left', 'work_count')

    def __init__(self, timer: 'PomodoroTimer'):
        self.timer = timer

    @property
    def serializable_data(self) -> Dict[str, Any]:
        self.timer.stop()
        return {attribute: getattr(self.timer, attribute)
                for attribute in self.serializable_attributes}

    def set_serialized_timer_data(self, data: Mapping) -> None:
        for attribute in self.serializable_attributes:
            try:
                value = data[attribute]
            except KeyError:
                logger.warning(f"Serialized attribute {attribute} couldn't be read (this might"
                               f" happen between updates)")
            else:
                setattr(self.timer, attribute, value)
