from contextlib import contextmanager
from curses import wrapper, echo, noecho, cbreak, nocbreak, newwin, error
from curses.textpad import rectangle
from math import floor
from subprocess import run, PIPE


def input_char(textbox_window):
    textbox_window.clear()
    return textbox_window.getkey(*textbox_window.getyx())


@contextmanager
def echo_nocbreak():
    echo()
    nocbreak()
    yield
    noecho()
    cbreak()


def input_sequence(textbox_window, status_window, status):
    write_status(status_window, status + " (or Ctrl-C to cancel)")
    textbox_window.clear()

    with echo_nocbreak():
        key_sequence = textbox_window.getstr(*textbox_window.getyx())

    return key_sequence


def toggle_pomodoro():
    pass


def stop():
    pass




def delete(task_window, textbox_window, status_window):
    number_is_valid = False
    number = input_sequence(textbox_window, status_window,
                            "Enter the task's number")

    while not number_is_valid:
        try:
            int(number)
        except ValueError:
            number = input_sequence(textbox_window, status_window,
                                    "Please enter a valid number")
        else:
            number_is_valid = True

    run(['task', number, 'delete', 'rc.confirmation=off'], stdout=PIPE)

def add(task_window, textbox_window, status_window):
    name = input_sequence(textbox_window, status_window,
                          "Enter the task's name")
    run(['task', 'add', name], stdout=PIPE)




def quit_():
    quit()
def custom_command(task_window, textbox_window, status_window):
    command = input_sequence(textbox_window, status_window, 'Enter your command')

    run(['task'] + command.split(), stdout=PIPE)


def refresh_tasks(task_window):
    tasks = run(['task'], stdout=PIPE).stdout.decode('utf-8').split("\n")

    for y, task in enumerate(tasks):
        task_window.addstr(y, 1, task)

    task_window.refresh()


def write_status(status_window, status):
    status_window.clear()
    status_window.addstr(status)
    status_window.refresh()


def newborderedwin(height, width, start_y, start_x):
    borderedwindow = newwin(height, width, start_y, start_x)
    borderedwindow.clear()
    borderedwindow.border()
    borderedwindow.refresh()

    return newwin(height - 2, width - 2, start_y + 1, start_x + 1)


def main(stdscr):
    stdscr.clear()

    MAX_Y, MAX_X = stdscr.getmaxyx()
    STATUS_WINDOW_HEIGHT = 5
    TEXTBOX_WINDOW_HEIGHT = 4
    TASK_WINDOW_HEIGHT = MAX_Y - STATUS_WINDOW_HEIGHT - TEXTBOX_WINDOW_HEIGHT

    task_window = newborderedwin(TASK_WINDOW_HEIGHT, MAX_X - 1,
                                 0, 0)
    status_window = newborderedwin(STATUS_WINDOW_HEIGHT, MAX_X - 1,
                                   TASK_WINDOW_HEIGHT, 0)
    textbox_window = newborderedwin(TEXTBOX_WINDOW_HEIGHT, MAX_X - 1,
                                    TASK_WINDOW_HEIGHT + STATUS_WINDOW_HEIGHT, 0)

    refresh_tasks(task_window)

    while True:
        try:
            write_status(status_window, '(r)efresh tasks, (a)dd task, '
                         '(d)elete task, (!) custom command, (p)omodoro (toggle)'
                         ', (s)top pomodoro, (q)uit')
            read_char = input_char(textbox_window)

            task_actions = {
                'r': refresh_tasks,
            }
            task_status_textbox_actions = {
                'a': add,
                'd': delete,
                '!': custom_command,
            }
            other_actions = {
                'p': toggle_pomodoro,
                's': stop,
                'q': quit_,
            }

            try:
                task_actions[read_char](task_window)
                task_window.refresh()
                continue
            except KeyError:
                pass

            try:
                action = task_status_textbox_actions[read_char]
                action(task_window, textbox_window, status_window)
                refresh_tasks(task_window)
                continue
            except KeyError:
                pass

            try:
                other_actions[read_char]()
            except KeyError:
                write_status(status_window, f'Unknown action: "{read_char}". '
                             'Press any key to continue')
                input_char(textbox_window)

        except KeyboardInterrupt:
            quit_()

wrapper(main)
