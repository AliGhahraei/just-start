from abc import ABC, abstractmethod
from functools import wraps
from inspect import isclass
from typing import Callable, Union, Optional

from ._log import log
from .constants import SYNC_MSG
from .os_utils import get_task_list, run_task, JustStartError


NOT_IMPLEMENTED_FUNCTION = "Client didn't implement this function"
INVALID_FUNCTION = 'Not a valid client function'


class ClientError(JustStartError, ValueError):
    pass


class BaseClient(ABC):
    @abstractmethod
    def write_status(self, status: str) -> None:
        pass

    @abstractmethod
    def write_pomodoro_status(self, status: str) -> None:
        pass

    @abstractmethod
    def on_tasks_refresh(self, task_list) -> None:
        pass


class _ClientImpl:
    def __init__(self):
        super().__setattr__('functions', {})

    def __getattr__(self, item) -> Callable:
        return self.functions[item]

    def __setattr__(self, key: str, value: Callable):
        self.functions[key] = value


_client_abstractmethods = set()


def _dynamic_abstractmethod(f):
    _client_abstractmethods.add(f.__name__)

    @wraps(f)
    def wrapper(*args, **kwargs):
        self, *args = args
        implementation = getattr(self.client_impl, f.__name__)

        if f is implementation:
            raise NotImplementedError(f'{NOT_IMPLEMENTED_FUNCTION}:'
                                      f' {f.__name__}')

        implementation(*args, **kwargs)

    return wrapper


class Client(BaseClient):
    def __init__(self) -> None:
        self.client_impl = _ClientImpl()

    @_dynamic_abstractmethod
    def write_status(self, status: str) -> None:
        pass

    @_dynamic_abstractmethod
    def write_pomodoro_status(self, status: str) -> None:
        pass

    @_dynamic_abstractmethod
    def on_tasks_refresh(self, task_list) -> None:
        pass

    def implement_method(self, name: str, implementation: Callable):
        if name not in _client_abstractmethods:
            raise ClientError(f'{INVALID_FUNCTION}: {name}')

        setattr(self.client_impl, name, implementation)


client = Client()


def client_decorator(function_or_class_or_name: Union[Callable, str]):
    target_function_name = function_or_class_or_name

    if isclass(function_or_class_or_name):
        if client.client_impl.functions:
            log.warning(f'The following client methods were defined before'
                        f" class decoration and might be overridden:"
                        f' {", ".join(client.client_impl.functions)}')

        client.client_impl = function_or_class_or_name
        return function_or_class_or_name
    else:
        def decorator(user_function: Callable) -> Callable:
            client.implement_method(target_function_name, user_function)
            return user_function

        if callable(function_or_class_or_name):
            target_function_name = function_or_class_or_name.__name__
            return decorator(function_or_class_or_name)

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
