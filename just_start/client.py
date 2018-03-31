from typing import Callable, Union


NOT_IMPLEMENTED_MESSAGE = 'Client should implement this function'
INVALID_CLIENT_MESSAGE = 'Not a valid client function'


class _Client(dict):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def write_status(status: str, error: bool=False) -> None:
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    @staticmethod
    def write_pomodoro_status(status: str, error: bool=False) -> None:
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    @staticmethod
    def prompt_char(prompt: str, error: bool=False) -> str:
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    @staticmethod
    def prompt_string(prompt: str, error: bool=False) -> str:
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    @staticmethod
    def on_tasks_refresh(task_list) -> None:
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    def __setitem__(self, key: str, value: Callable):
        if key not in _Client.__dict__:
            raise ValueError(f'{INVALID_CLIENT_MESSAGE}: {key}')
        self.__setattr__(key, value)


client = _Client()


def client_decorator(user_function: Union[Callable, str]):
    local_function_name = None

    def decorator(user_function_: Callable) -> Callable:
        client[local_function_name] = user_function_
        return user_function_

    if callable(user_function):
        local_function_name = user_function.__name__
        return decorator(user_function)

    local_function_name = user_function
    return decorator
