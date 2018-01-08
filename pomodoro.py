from datetime import datetime, timedelta
from enum import Enum
from itertools import cycle
from subprocess import run
from threading import Timer


WORK_TIME = 45
SHORT_REST_TIME = 15
LONG_REST_TIME = 60
CYCLES_BEFORE_LONG_REST = 3


def end_time(time_left):
    end_time = datetime.now() + timedelta(seconds=time_left)
    return end_time.strftime('%H:%M')


class State(Enum):
    WORK = 'Work', WORK_TIME * 60
    SHORT_REST = 'Short rest', SHORT_REST_TIME * 60
    LONG_REST = 'LONG REST!!!',  LONG_REST_TIME * 60


class PomodoroTimer():
    def __init__(self, external_status_function, external_blocking_function):
        states = [State.WORK, State.SHORT_REST] * CYCLES_BEFORE_LONG_REST
        states[-1] = State.LONG_REST

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
        run(['notify-send', status])
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
            self.external_blocking_function(blocked=self.state is State.WORK)

        self.is_running = not self.is_running

    def _run(self):
        self.start_datetime = datetime.now()
        self.write_status(f'{self.state.value[0]} ({self.work_count} pomodoros'
                          f' so far). End time: {end_time(self.time_left)}')

        self.timer = Timer(self.time_left,
                           self.next_phase)
        self.timer.start()

    def _update_state(self):
        self.state = self.POMODORO_CYCLE.__next__()
        self.time_left = self.state.value[1]

    def next_phase(self):
        self._stop_countdown()
        self.is_running = True

        if self.state is State.WORK:
            self.work_count += 1

        self._update_state()
        self._run()

        self.external_blocking_function(blocked=self.state is State.WORK)

    def reset(self):
        self._stop_countdown()
        self.__init__(self.external_status_function,
                      self.external_blocking_function)
        self.external_blocking_function(blocked=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop_countdown()
        self.external_blocking_function(blocked=True)

    def _stop_countdown(self):
        if self.is_running:
            self.timer.cancel()
