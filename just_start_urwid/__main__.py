from just_start_urwid.client import (
    handle_loop_exceptions, create_main_loop, TopWidget, columns, pomodoro_status_box,
)


top = TopWidget(columns, footer=pomodoro_status_box)


def main():
    with handle_loop_exceptions():
        create_main_loop(top).run()


if __name__ == '__main__':
    main()
