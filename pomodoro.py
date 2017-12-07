from datetime import datetime
from enum import Enum
from itertools import cycle
from subprocess import run
from threading import Timer


WORK_TIME = 45
SHORT_REST_TIME = 15
LONG_REST_TIME = 60
CYCLES_BEFORE_LONG_REST = 3


class State(Enum):
    WORK = 'Work', WORK_TIME * 60
    SHORT_REST = 'Short rest', SHORT_REST_TIME * 60
    LONG_REST = 'LONG REST!!!',  LONG_REST_TIME * 60


class PomodoroTimer():
    def __init__(self):
        states = [State.WORK, State.SHORT_REST] * CYCLES_BEFORE_LONG_REST
        states.append(State.LONG_REST)

        self.POMODORO_CYCLE = cycle(states)
        self._update_state()
        self.is_running = False
        self.start_datetime = self.timer = None

    def toggle(self):
        if self.is_running:
            self.timer.cancel()

            elapsed_timedelta = datetime.now() - self.start_datetime
            self.time_left -= elapsed_timedelta.seconds

            run(['notify-send', 'Paused'])
        else:
            self._run()

        self.is_running = not self.is_running

    def _run(self):
        self.start_datetime = datetime.now()
        run(['notify-send', self.state.value[0]])

        self.timer = Timer(self.time_left,
                           self.next_phase)
        self.timer.start()

    def _update_state(self):
        self.state = self.POMODORO_CYCLE.__next__()
        self.time_left = self.state.value[1]

    def next_phase(self):
        self._stop_countdown()
        self.is_running = True
        self._update_state()
        self._run()

    def reset(self):
        self._stop_countdown()
        self.__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop_countdown()

    def _stop_countdown(self):
        if self.is_running:
            self.timer.cancel()
