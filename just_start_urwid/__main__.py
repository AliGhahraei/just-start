from just_start import just_start
from just_start_urwid.client import create_main_loop, create_top_widget


def main():
    with just_start():
        create_main_loop(create_top_widget()).run()


if __name__ == '__main__':
    main()
