from just_start_urwid.client import (
    handle_loop_exceptions, create_main_loop, create_top_widget,
)


def main():
    with handle_loop_exceptions():
        create_main_loop(create_top_widget()).run()


if __name__ == '__main__':
    main()
