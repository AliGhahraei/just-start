import shelve
from collections.abc import MutableMapping
from pickle import HIGHEST_PROTOCOL
from platform import system
from subprocess import run, PIPE, STDOUT
from typing import List, Callable

from pexpect import spawn, EOF

from .config_reader import get_general_config, GeneralConfig
from .constants import PERSISTENT_PATH
from ._log import log


BLOCKING_IP = get_general_config().blocking_ip

APP_SPECIFIC_COMMENT = '# just-start'
BLOCKING_LINES = '\\n'.join(
    [f'{BLOCKING_IP}\\t{blocked_site}\\t{APP_SPECIFIC_COMMENT}\\n'
     f'{BLOCKING_IP}\\twww.{blocked_site}\\t{APP_SPECIFIC_COMMENT}'
     for blocked_site in get_general_config().blocked_sites])
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
    # Blocked sites could be outdated, so unblock and re-block
    run_sudo(UNBLOCK_COMMAND)

    if block:
        run_sudo(BLOCK_COMMAND)


def notify(status: str) -> None:
    notification_command_args = (('notify-send', status) if system() == 'Linux'
                                 else ('osascript', '-e', f'display notification "{status}"'
                                                          f' with title "just-start"'))
    run_command(*notification_command_args)


def run_command(*args):
    return run(args, stdout=PIPE, stderr=STDOUT)


def run_task(*args) -> str:
    args = args or ['-BLOCKED']
    completed_process = run_command('task', *args)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output


def run_sudo(command: str, config_getter: Callable[[], GeneralConfig] = get_general_config) -> None:
    password = config_getter().password
    if password:
        _run_with_password(command, password)


def _run_with_password(command: str, password: str):
    try:
        _spawn_sudo_command(command, password)
    except OSError:
        log.exception(f'"{command}" command failed')


def _spawn_sudo_command(command, password):
    child = spawn(command)
    child.sendline(password)
    child.expect(EOF)


class Db(MutableMapping):
    def __init__(self, db_opener: Callable = shelve.open):
        self._db_opener = db_opener

    def __getitem__(self, item):
        with self._db_opener(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            return db_[item]

    def __setitem__(self, key, value):
        with self._db_opener(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            db_[key] = value

    def __delitem__(self, key):  # pragma: no cover
        raise NotImplementedError

    def __iter__(self):  # pragma: no cover
        raise NotImplementedError

    def __len__(self):  # pragma: no cover
        raise NotImplementedError

    def update(self, *args, **kwargs):
        with self._db_opener(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            db_.update(*args, **kwargs)


db = Db()
