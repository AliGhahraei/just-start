from urwid import MainLoop

import just_start.constants as const
from just_start import quit_just_start, log
from just_start_urwid.client import top, _get_error_colors


def main():
    try:
        MainLoop(
            top,
            palette=(
                ('error', *_get_error_colors()),
            )
        ).run()
    except KeyboardInterrupt:
        quit_just_start(exit_message_func=print)
    except Exception as ex:
        print(const.UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH.format(ex))
        log.exception(const.UNHANDLED_ERROR)
        quit_just_start(exit_message_func=print)


if __name__ == '__main__':
    main()
