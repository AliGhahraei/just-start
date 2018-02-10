#!/usr/bin/env python3

from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
from os.path import expanduser
from platform import system
from subprocess import run
from threading import Timer

import yaml


def end_time_from_now(seconds_left):
    end_time = datetime.now() + timedelta(seconds=seconds_left)
    return end_time.strftime('%H:%M')


class PomodoroException(Exception):
    pass


class PomodoroTimer:
    def __init__(self, external_status_function, external_blocking_function,
                 config, config_location):
        self.config = config
        self.config_location = config_location
        self.external_status_function = external_status_function

        duration_config = (config['work_duration'] if self.user_is_at_work()
                           else config['home_duration'])

        work_time = duration_config['work']
        short_rest_time = duration_config['short_rest']
        long_rest_time = duration_config['long_rest']
        cycles_before_long_rest = duration_config['cycles_before_long_rest']

        self.state = Enum('state', [
            ('WORK', ('Work', work_time * 60)),
            ('SHORT_REST', ('Short rest', short_rest_time * 60)),
            ('LONG_REST', ('LONG REST!!!',  long_rest_time * 60))
        ])

        states = ([self.state.WORK, self.state.SHORT_REST]
                  * cycles_before_long_rest)
        states[-1] = self.state.LONG_REST

        self.POMODORO_CYCLE = cycle(states)
        self.external_blocking_function = external_blocking_function
        self.work_count = 0
        self._update_state()
        self.is_running = False
        self.start_datetime = self.timer = None
        self.notify('Pomodoro timer stopped')

    def notify(self, status):
        if system() == 'Linux':
            run(['notify-send', status])
        else:
            run(['osascript', '-e',
                 f'display notification "{status}" with title'
                 f' "just-start"'])
        self.external_status_function(status)

    def user_is_at_work(self):
        work_start = self.config['work']['start_time']
        work_end = self.config['work']['end_time']

        return datetime.now().weekday() < 5 and (
                datetime.strptime(work_start, '%H:%M').time()
                <= datetime.now().time()
                <= datetime.strptime(work_end, '%H:%M').time()
        )

    def toggle(self):
        if self.is_running:
            self.timer.cancel()

            elapsed_timedelta = datetime.now() - self.start_datetime
            self.time_left -= elapsed_timedelta.seconds

            self.notify('Paused')
            self.external_blocking_function(blocked=True)
        else:
            self._run()
            self.external_blocking_function(blocked=self.state
                                            is self.state.WORK)

        self.is_running = not self.is_running

    def _run(self):
        self.start_datetime = datetime.now()
        self.notify(f'{self.state.value[0]} ({self.work_count} pomodoros so'
                    f' far). End time: {end_time_from_now(self.time_left)}'
                    f' ({int(self.time_left / 60)} mins). You are at'
                    f' {"work" if self.user_is_at_work() else "home"}')

        self.timer = Timer(self.time_left,
                           self._timer_triggered_phase_advancement)
        self.timer.start()

    def _update_state(self):
        self.state = self.POMODORO_CYCLE.__next__()
        self.time_left = self.state.value[1]

    def _timer_triggered_phase_advancement(self):
        self.advance_phases(timer_triggered=True)

    def advance_phases(self, timer_triggered=False, phases_skipped=1):
        if self.state is self.state.WORK:
            if not timer_triggered and not (self.config['productivity']
                                            ['work_skip_enabled']):
                raise PomodoroException('Sorry, please work 1 pomodoro to'
                                        ' re-enable work skipping')

            self.work_count += 1
            self.config['productivity']['work_skip_enabled'] = timer_triggered

            with open(expanduser(self.config_location), 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        elif phases_skipped > 1:
            raise PomodoroException("Sorry, you can't skip more than 1 phase"
                                    " while not working")

        self._stop_countdown()
        self.is_running = True

        for _ in range(phases_skipped):
            self._update_state()
        self._run()

        self.external_blocking_function(blocked=self.state is self.state.WORK)

    def reset(self):
        self._stop_countdown()
        self.__init__(self.external_status_function,
                      self.external_blocking_function, self.config,
                      self.config_location)
        self.external_blocking_function(blocked=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop_countdown()
        self.external_blocking_function(blocked=True)

    def _stop_countdown(self):
        if self.is_running:
            self.timer.cancel()
