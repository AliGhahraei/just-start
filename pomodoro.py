from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
from os.path import expanduser
from platform import system
from subprocess import run
from threading import Timer

import yaml


def end_time(time_left):
    end_time = datetime.now() + timedelta(seconds=time_left)
    return end_time.strftime('%H:%M')


class PomodoroTimer():
    def __init__(self, external_status_function, external_blocking_function,
                 config, config_location):
        self.config = config
        self.config_location = config_location

        is_work_time = (datetime.strptime(config['work']['start_time'],
                                          '%H:%M').time()
                        <= datetime.now().time()
                        <= (datetime.strptime(config['work']['end_time'],
                                              '%H:%M')).time())

        duration_config = (config['work_duration'] if datetime.now().weekday()
                           < 5 and is_work_time else config['home_duration'])

        WORK_TIME = duration_config['work']
        SHORT_REST_TIME = duration_config['short_rest']
        LONG_REST_TIME = duration_config['long_rest']
        CYCLES_BEFORE_LONG_REST = duration_config['cycles_before_long_rest']

        self.State = Enum('State', [
            ('WORK', ('Work', WORK_TIME * 60)),
            ('SHORT_REST', ('Short rest', SHORT_REST_TIME * 60)),
            ('LONG_REST', ('LONG REST!!!',  LONG_REST_TIME * 60))
        ])

        states = ([self.State.WORK, self.State.SHORT_REST]
                  * CYCLES_BEFORE_LONG_REST)
        states[-1] = self.State.LONG_REST

        self.POMODORO_CYCLE = cycle(states)
        self.external_status_function = external_status_function
        self.external_blocking_function = external_blocking_function
        self.work_count = 0
        self._update_state()
        self.is_running = False
        self.start_datetime = self.timer = None
        self.write_status('Pomodoro timer stopped')

    def write_status(self, status):
        self.written_status = status
        if system() == 'Linux':
            run(['notify-send', status])
        else:
            run(['osascript', '-e', f'display notification "{status}" with'
                 ' title "just-start"'])
        self.external_status_function(status)

    def toggle(self):
        if self.is_running:
            self.timer.cancel()

            elapsed_timedelta = datetime.now() - self.start_datetime
            self.time_left -= elapsed_timedelta.seconds

            self.write_status('Paused')
            self.external_blocking_function(blocked=True)
        else:
            self._run()
            self.external_blocking_function(blocked=self.state
                                            is self.State.WORK)

        self.is_running = not self.is_running

    def _run(self):
        self.start_datetime = datetime.now()
        self.write_status(f'{self.state.value[0]} ({self.work_count} pomodoros'
                          f' so far). End time: {end_time(self.time_left)}'
                          f' ({int(self.time_left / 60)} mins)')

        self.timer = Timer(self.time_left,
                           self._timer_triggered_skip_phases)
        self.timer.start()

    def _update_state(self):
        self.state = self.POMODORO_CYCLE.__next__()
        self.time_left = self.state.value[1]

    def _timer_triggered_skip_phases(self):
        self.skip_phases(timer_triggered=True)

    def skip_phases(self, timer_triggered=False, phases_skipped=1):
        if self.state is self.State.WORK:
            if not timer_triggered and not (self.config['productivity']
                                            ['work_skip_enabled']):
                self.write_status('Sorry, please work 1 pomodoro to reenable'
                                  ' work skipping')
                return False

            self.work_count += 1
            self.config['productivity']['work_skip_enabled'] = timer_triggered

            with open(expanduser(self.config_location), 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        elif phases_skipped > 1:
            self.write_status("Sorry, you can't skip more than 1 phase while"
                              " not working")
            return False

        self._stop_countdown()
        self.is_running = True

        for _ in range(phases_skipped):
            self._update_state()
        self._run()

        self.external_blocking_function(blocked=self.state is self.State.WORK)

        return True

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
