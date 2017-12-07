from datetime import datetime
from itertools import cycle
from subprocess import run
from threading import Timer


WORK_TIME = 45
SHORT_REST_TIME = 15
LONG_REST_TIME = 60
CYCLES_BEFORE_LONG_REST = 3


class PomodoroTimer():
    def __init__(self):
        self.POMODORO_CYCLE = cycle([('Work', WORK_TIME * 60),
                                     ('Short rest', SHORT_REST_TIME * 60)]
                                    * CYCLES_BEFORE_LONG_REST
                                    + [('LONG REST!!!', LONG_REST_TIME * 60)])
        self.state, self.time_left = self.POMODORO_CYCLE.__next__()
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
        run(['notify-send', self.state])

        self.timer = Timer(self.time_left,
                           self.next_phase)
        self.timer.start()

    def next_phase(self):
        self.timer.cancel()
        self.state, self.time_left = self.POMODORO_CYCLE.__next__()
        self._run()

    def reset(self):
        self.timer.cancel()
        self.__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_running:
            self.timer.cancel()
