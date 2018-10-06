from abc import ABCMeta
from functools import partial
from typing import Callable, Any


class Singleton(metaclass=ABCMeta):
    _instance = None

    def __init__(self, init_instance: Callable, *args, **kwargs):
        self._init_instance = partial(init_instance, *args, **kwargs)

    def __getattr__(self, item: str) -> Any:
        try:
            return self._get_instance_attr(item)
        except AttributeError:
            if type(self)._instance is not None:
                raise
            type(self)._instance = self._init_instance()
            return self._get_instance_attr(item)

    @classmethod
    def _get_instance_attr(cls, item: str):
        return getattr(cls._instance, item)
