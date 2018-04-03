from typing import Callable, Union


NOT_IMPLEMENTED_FUNCTION = "Client didn't implement this function"
INVALID_FUNCTION = 'Not a valid client function'


class Client(dict):
    def __init__(self) -> None:
        super().__init__()

    def write_status(self, status: str, error: bool=False) -> None:
        raise NotImplementedError(NOT_IMPLEMENTED_FUNCTION)

    def write_pomodoro_status(self, status: str, error: bool=False) -> None:
        raise NotImplementedError(NOT_IMPLEMENTED_FUNCTION)

    def prompt(self, message: str) -> str:
        raise NotImplementedError(NOT_IMPLEMENTED_FUNCTION)

    def on_tasks_refresh(self, task_list) -> None:
        raise NotImplementedError(NOT_IMPLEMENTED_FUNCTION)

    def __setitem__(self, key: str, value: Callable):
        if key not in Client.__dict__:
            raise ValueError(f'{INVALID_FUNCTION}: {key}')
        self.__setattr__(key, value)


client = Client()


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
