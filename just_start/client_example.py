from just_start import (
    initial_refresh_and_sync, client, UNARY_ACTION_KEYS, NULLARY_ACTION_KEYS,
    JustStartError, PromptSkippedPhases, Action, UNARY_ACTION_MESSAGES,
    UserInputError, quit_just_start
)
from just_start.constants import (
    EMPTY_STRING, ACTION_PROMPT, INVALID_ACTION_KEY, SKIPPED_PHASES_PROMPT,
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


def prompt(prompt_):
    user_input = input(f'{prompt_}\n')
    if user_input == '':
        raise UserInputError(EMPTY_STRING)
    return user_input


def main():
    initial_refresh_and_sync(sync_error_func=error)

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


def run_action(key):
    try:
        action = NULLARY_ACTION_KEYS[key]
    except KeyError:
        try:
            action = UNARY_ACTION_KEYS[key]
        except KeyError:
            raise UserInputError(f'{INVALID_ACTION_KEY} "{key}"')

        prompt_message = UNARY_ACTION_MESSAGES[action]
        arg = prompt(prompt_message)
        action(arg)
    else:
        try:
            action()
        except PromptSkippedPhases:
            phases = prompt(SKIPPED_PHASES_PROMPT)
            Action.SKIP_PHASES(phases=phases)


if __name__ == '__main__':
    main()
