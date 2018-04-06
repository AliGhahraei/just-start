from just_start import (
    initial_refresh_and_sync, client, UNARY_ACTION_KEYS, NULLARY_ACTION_KEYS,
    JustStartError, PromptSkippedPhases, Action, KEYBOARD_INTERRUPT_MESSAGE)

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
    try:
        initial_refresh_and_sync()
    except JustStartError as e:
        error(e)

    while True:
        try:
            key = input('Enter your action\n')
            try:
                action = NULLARY_ACTION_KEYS[key]
            except KeyError:
                try:
                    action = UNARY_ACTION_KEYS[key]
                except KeyError:
                    error(f'Invalid key action "{key}"')
                else:
                    messages = {
                        Action.ADD: "Enter the task's data",
                        Action.LOCATION_CHANGE: "Enter 'w' for work or anything"
                                                " else for home",
                        Action.CUSTOM_COMMAND: "Enter your custom command"
                    }

                    ids = input('Enter the ids\n')
                    action(ids)
            except PromptSkippedPhases:
                phases = input('How many phases?')
                Action.SKIP_PHASES(phases=phases)
            else:
                action()
        except KeyboardInterrupt:
            error(KEYBOARD_INTERRUPT_MESSAGE)
        except JustStartError as e:
            error(e)


if __name__ == '__main__':
    main()
