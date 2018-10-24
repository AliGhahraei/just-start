import sys

from just_start import (
    UNARY_ACTION_KEYS, NULLARY_ACTION_KEYS, JustStartError, UNARY_ACTION_PROMPTS,
    UserInputError, just_start, ActionRunner, Action
)
from just_start.constants import (
    EMPTY_STRING, ACTION_PROMPT, INVALID_ACTION_KEY, TASK_IDS_PROMPT,
)

RESTORE_COLOR = '\033[0m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RED = '\033[91m'


def on_tasks_refresh(task_list):
    print('\n'.join(task_list))


def write_status(message):
    print(f'{GREEN}{message}{RESTORE_COLOR}')


def write_pomodoro_status(message):
    print(f'{BLUE}{message}{RESTORE_COLOR}')


def error(message):
    print(f'{RED}{message}{RESTORE_COLOR}', file=sys.stderr)


def prompt(prompt_):  # pragma: no cover
    user_input = input(f'{prompt_}\n')
    if user_input == '':
        raise UserInputError(EMPTY_STRING)
    return user_input


def main():
    with just_start(write_status, on_tasks_refresh, write_pomodoro_status) as action_runner:
        read_keys(action_runner)


def read_keys(action_runner: ActionRunner):
    while True:
        try:
            key = prompt(ACTION_PROMPT)
            if key == 'q':
                break

            run_action(action_runner, key)
        except JustStartError as e:
            error(e)


def run_action(action_runner: ActionRunner, key):
    try:
        action = NULLARY_ACTION_KEYS[key]
    except KeyError:
        try:
            action = UNARY_ACTION_KEYS[key]
        except KeyError:
            raise UserInputError(f'{INVALID_ACTION_KEY} "{key}"')

        prompt_message = UNARY_ACTION_PROMPTS[action]
        args = [prompt(prompt_message)]

        if action is Action.MODIFY:
            args.append(prompt(TASK_IDS_PROMPT))

        action_runner(action, *args)
    else:
        action_runner(action)


if __name__ == '__main__':
    main()
