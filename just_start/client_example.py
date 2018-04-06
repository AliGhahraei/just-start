from just_start import (
    initial_refresh_and_sync, client, UNARY_ACTION_KEYS, NULLARY_ACTION_KEYS,
    JustStartError, PromptSkippedPhases, Action, KEYBOARD_INTERRUPT_MESSAGE,
    UNARY_ACTIONS)

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


def main():
    initial_refresh_and_sync(error=error)

    while True:
        try:
            key = input('Enter your action\n')
        except KeyboardInterrupt:
            error(KEYBOARD_INTERRUPT_MESSAGE)
        else:
            try:
                run_action(key)
            except (JustStartError, ValueError) as e:
                error(e)
            except KeyboardInterrupt:
                pass


def run_action(key):
    try:
        action = NULLARY_ACTION_KEYS[key]
    except KeyError:
        try:
            action = UNARY_ACTION_KEYS[key]
        except KeyError:
            raise ValueError(f'Invalid key action "{key}"')

        prompt_message = UNARY_ACTIONS[action]
        arg = input(f'{prompt_message}\n')
        action(arg)
    else:
        try:
            action()
        except PromptSkippedPhases:
            phases = input('How many phases do you want to skip?')
            Action.SKIP_PHASES(phases=phases)


if __name__ == '__main__':
    main()
