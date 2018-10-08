from traceback import format_exc

from just_start import (
    init_gui, client, UNARY_ACTION_KEYS, NULLARY_ACTION_KEYS,
    JustStartError, PromptSkippedPhases, Action, UNARY_ACTIONS,
    UserInputError, quit_just_start, init, log
)
from just_start.constants import (
    EMPTY_STRING, ACTION_PROMPT, INVALID_ACTION_KEY, SKIPPED_PHASES_PROMPT,
    TASK_IDS_PROMPT, UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH, UNHANDLED_ERROR
)

RESTORE_COLOR = '\033[0m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RED = '\033[91m'


@client
def on_tasks_refresh(task_list):
    print('\n'.join(task_list))


@client
def write_status(message):
    print(f'{GREEN}{message}{RESTORE_COLOR}')


@client
def write_pomodoro_status(message):
    print(f'{BLUE}{message}{RESTORE_COLOR}')


def error(message):
    print(f'{RED}{message}{RESTORE_COLOR}')


def prompt(prompt_):  # pragma: no cover
    user_input = input(f'{prompt_}\n')
    if user_input == '':
        raise UserInputError(EMPTY_STRING)
    return user_input


def main():
    try:
        init()
        init_gui(sync_error_func=error)

        try:
            while True:
                try:
                    key = prompt(ACTION_PROMPT)
                    if key == 'q':
                        break

                    run_action(key)
                except JustStartError as e:
                    error(e)
        except KeyboardInterrupt:
            pass

        quit_just_start(exit_message_func=print, sync_error_func=exit)
    except Exception as ex:
        print(UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH.format(ex))
        log.exception(UNHANDLED_ERROR)


def run_action(key):
    try:
        action = NULLARY_ACTION_KEYS[key]
    except KeyError:
        try:
            action = UNARY_ACTION_KEYS[key]
        except KeyError:
            raise UserInputError(f'{INVALID_ACTION_KEY} "{key}"')

        prompt_message = UNARY_ACTIONS[action]
        args = [prompt(prompt_message)]

        if action is Action.MODIFY:
            args.append(prompt(TASK_IDS_PROMPT))

        action(*args)
    else:
        try:
            action()
        except PromptSkippedPhases:
            phases = prompt(SKIPPED_PHASES_PROMPT)
            Action.SKIP_PHASES(phases=phases)


if __name__ == '__main__':
    main()
