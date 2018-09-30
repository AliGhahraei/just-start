import shelve
from collections import MutableMapping
from pickle import HIGHEST_PROTOCOL
from subprocess import run, PIPE, STDOUT
from typing import List

from pexpect import spawn, EOF

from .config_reader import get_config
from .constants import PERSISTENT_PATH


BLOCKING_IP = get_config().general.blocking_ip

APP_SPECIFIC_COMMENT = '# just-start'
BLOCKING_LINES = '\\n'.join(
    [f'{BLOCKING_IP}\\t{blocked_site}\\t{APP_SPECIFIC_COMMENT}\\n'
     f'{BLOCKING_IP}\\twww.{blocked_site}\\t{APP_SPECIFIC_COMMENT}'
     for blocked_site in get_config().general.blocked_sites])
BLOCK_COMMAND = (f'/bin/bash -c "echo -e \'{BLOCKING_LINES}\' | sudo tee -a'
                 f' /etc/hosts > /dev/null"')
UNBLOCK_COMMAND = f"sudo sed -i '' '/^.*{APP_SPECIFIC_COMMENT}$/d' /etc/hosts"


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ActionError(JustStartError):
    pass


class UserInputError(JustStartError, ValueError):
    pass


def get_task_list() -> List[str]:
    return run_task().split("\n")


def block_sites(block: bool) -> None:
    # Always delete outdated blocked sites
    run_sudo(UNBLOCK_COMMAND)

    if block:
        run_sudo(BLOCK_COMMAND)


def run_command(*args):
    return run(args, stdout=PIPE, stderr=STDOUT)


def run_task(*args) -> str:
    args = args or ['-BLOCKED']
    completed_process = run_command('task', *args)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output


def run_sudo(command: str) -> None:
    password = get_config().general.password
    if password:
        child = spawn(command)

        try:
            child.sendline(password)
            child.expect(EOF)
        except OSError:
            pass


class Db(MutableMapping):
    def __getitem__(self, item):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            return db_[item]

    def __setitem__(self, key, value):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            db_[key] = value

    def __delitem__(self, key):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            del db_[key]

    def __iter__(self):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            yield iter(db_)

    def __len__(self):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            return len(db_)

    def __str__(self):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            return str({key: value for key, value in db_.items()})

    def update(*args):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            # method doesn't expect self argument
            db_.update(*args[1:])


db = Db()
