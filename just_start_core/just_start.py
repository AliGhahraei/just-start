from subprocess import run, PIPE, STDOUT
from typing import List, Optional


class JustStartError(Exception):
    pass


class TaskWarriorError(JustStartError):
    pass


class ConfigurationMissingError(JustStartError, FileNotFoundError):
    pass


class ActionError(JustStartError):
    pass


def run_task(arg_list: Optional[List[str]]=None) -> str:
    arg_list = arg_list or []
    completed_process = run(['task'] + arg_list, stdout=PIPE, stderr=STDOUT)
    process_output = completed_process.stdout.decode('utf-8')

    if completed_process.returncode != 0:
        raise TaskWarriorError(process_output)

    return process_output
