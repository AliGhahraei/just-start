import shelve
from pickle import HIGHEST_PROTOCOL
from platform import system
from subprocess import run, PIPE, STDOUT
from typing import List

from pexpect import spawn, EOF

from .config_reader import config
from .constants import PERSISTENT_PATH


PASSWORD = config['general']['password']
BLOCKING_IP = config['general']['blocking_ip']

APP_SPECIFIC_COMMENT = '# just-start'
# noinspection SpellCheckingInspection
BLOCKING_LINES = '\\n'.join(
    [f'{BLOCKING_IP}\\t{blocked_site}\\t{APP_SPECIFIC_COMMENT}\\n'
     f'{BLOCKING_IP}\\twww.{blocked_site}\\t{APP_SPECIFIC_COMMENT}'
     for blocked_site in config['general']['blocked_sites']])
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
    run_sudo(UNBLOCK_COMMAND, PASSWORD)

    if block:
        run_sudo(BLOCK_COMMAND, PASSWORD)


def manage_wifi(*, enable: bool=False) -> None:
    if enable:
        if system() == 'Linux':
            # noinspection SpellCheckingInspection
            run_sudo('sudo systemctl start netctl-auto@wlp2s0', PASSWORD)
        else:
            # noinspection SpellCheckingInspection
            run_sudo('networksetup -setairportpower en0 on', PASSWORD)
    else:
        if system() == 'Linux':
            # noinspection SpellCheckingInspection
            run_sudo('sudo systemctl stop netctl-auto@wlp2s0', PASSWORD)
        else:
            # noinspection SpellCheckingInspection
            run_sudo('networksetup -setairportpower en0 off', PASSWORD)


def run_command(*args):
    return run(args, stdout=PIPE, stderr=STDOUT)


def run_task(*args) -> str:
    args = args or ['-BLOCKED']
    completed_process = run_command('task', *args)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output


def run_sudo(command: str, password: str) -> None:
    if password:
        child = spawn(command)

        try:
            child.sendline(password)
            child.expect(EOF)
        except OSError:
            pass


class Db(dict):
    def __getitem__(self, item):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            return db_[item]

    def __setitem__(self, key, value):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            db_[key] = value

    def update(self, __m, **kwargs):
        with shelve.open(PERSISTENT_PATH, protocol=HIGHEST_PROTOCOL) as db_:
            db_.update(__m, **kwargs)


db = Db()
