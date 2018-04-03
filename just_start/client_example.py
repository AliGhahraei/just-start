from just_start import (
    init, client, UNARY_ACTION_KEYS, NULLARY_ACTION_KEYS, JustStartError)

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
    init()

    while True:
        key = input('Enter your action\n')
        try:
            try:
                action = NULLARY_ACTION_KEYS[key]
            except KeyError:
                action = UNARY_ACTION_KEYS[key]
                ids = input('Enter the ids')
                action(ids)
            else:
                action()
        except JustStartError as e:
            error(e)


if __name__ == '__main__':
    main()
