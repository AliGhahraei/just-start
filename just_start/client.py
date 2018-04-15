from functools import wraps
from typing import Callable, Union, Optional

from .constants import SYNC_MSG
from .os import get_task_list, run_task, JustStartError


NOT_IMPLEMENTED_FUNCTION = "Client didn't implement this function"
INVALID_FUNCTION = 'Not a valid client function'


class ClientError(JustStartError, ValueError):
    pass


class Client(dict):
    def __init__(self) -> None:
        super().__init__()

    def write_status(self, status: str) -> None:
        raise NotImplementedError(f'{NOT_IMPLEMENTED_FUNCTION}:'
                                  f' {self.write_status.__name__}')

    def write_pomodoro_status(self, status: str) -> None:
        raise NotImplementedError(f'{NOT_IMPLEMENTED_FUNCTION}:'
                                  f' {self.write_pomodoro_status.__name__}')

    def on_tasks_refresh(self, task_list) -> None:
        raise NotImplementedError(f'{NOT_IMPLEMENTED_FUNCTION}:'
                                  f' {self.on_tasks_refresh.__name__}')

    def __setitem__(self, key: str, value: Callable):
        if key not in Client.__dict__:
            raise ClientError(f'{INVALID_FUNCTION}: {key}')
        self.__setattr__(key, value)


client = Client()


def client_decorator(user_function_or_name: Union[Callable, str]):
    target_function_name = user_function_or_name

    def decorator(user_function: Callable) -> Callable:
        client[target_function_name] = user_function
        return user_function

    if callable(user_function_or_name):
        target_function_name = user_function_or_name.__name__
        return decorator(user_function_or_name)

    return decorator


def refresh_tasks(f: Callable=None) -> Optional[Callable]:
    """Refresh tasks or decorate a function to call refresh after its code.

    :param f: call to execute before refreshing
    :return: a decorated refreshing function if used as decorator
    :raise TaskWarriorError if sync fails
    """

    if f:
        @wraps(f)
        def decorator(*args, **kwargs) -> None:
            f(*args, **kwargs)
            client.on_tasks_refresh(get_task_list())

        return decorator

    client.on_tasks_refresh(get_task_list())


class StatusManager:
    def __init__(self) -> None:
        self._pomodoro_status = ''
        self._status = ''

    @property
    def app_status(self) -> str:
        return self._status

    @app_status.setter
    def app_status(self, status) -> None:
        client.write_status(status)
        self._status = status

    @property
    def pomodoro_status(self) -> str:
        return self._pomodoro_status

    @pomodoro_status.setter
    def pomodoro_status(self, pomodoro_status) -> None:
        client.write_pomodoro_status(pomodoro_status)
        self._pomodoro_status = pomodoro_status

    @refresh_tasks
    def sync(self) -> None:
        self.app_status = SYNC_MSG
        self.app_status = run_task('sync')
