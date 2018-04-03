from typing import Callable, Union


NOT_IMPLEMENTED_FUNCTION = "Client didn't implement this function"
INVALID_FUNCTION = 'Not a valid client function'


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
