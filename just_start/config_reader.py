from datetime import time, datetime
from functools import partial
from os.path import expanduser
from typing import Dict, List, Generator, Callable, Any, Mapping, Iterator, Tuple, TypeVar, cast

from pydantic import BaseModel, UrlStr, PositiveInt, FilePath, conint
from toml import load

from .constants import CONFIG_PATH


WeekdayInt = conint(le=0, ge=6)


class _ClockTime(time):
    @classmethod
    def get_validators(cls) -> Generator[Callable, None, None]:
        yield cls.validate_format

    @classmethod
    def validate_format(cls, time_str: str) -> time:
        return datetime.strptime(time_str, '%H:%M').time()


class _LocationActivationConfig(BaseModel):
    start: _ClockTime
    end: _ClockTime
    days: List[WeekdayInt]


class GeneralConfig(BaseModel):
    password: str = None
    taskrc_path: FilePath = expanduser("~/.taskrc")
    blocked_sites: List[str] = []
    blocking_ip: UrlStr = "127.0.0.1"
    notifications: bool = True


class PomodoroConfig(BaseModel):
    pomodoro_length: PositiveInt = 25
    short_rest: PositiveInt = 5
    long_rest: PositiveInt = 15
    cycles_before_long_rest: PositiveInt = 4


class _LocationConfig(BaseModel):
    name: str
    activation: _LocationActivationConfig
    general: GeneralConfig = GeneralConfig()
    pomodoro: PomodoroConfig = PomodoroConfig()


class _FullConfig(BaseModel):
    general: GeneralConfig = GeneralConfig()
    pomodoro: PomodoroConfig = PomodoroConfig()
    locations: List[_LocationConfig] = []


Section = TypeVar('Section', bound=BaseModel)


class Config(Mapping):
    def __init__(self, **data):
        self._config = _FullConfig(**data)
        self._config_dict = self._config.dict()  # type: Dict
        self._at_work_override = False

    def __getitem__(self, item: str) -> Any:
        return getattr(self._config, item)

    def __iter__(self) -> Iterator[Tuple]:
        return iter(self._config_dict.items())

    def __len__(self) -> int:
        return len(self._config_dict)

    @property
    def general(self) -> GeneralConfig:
        return self._get_location_section_or_default('general')

    @property
    def pomodoro(self) -> PomodoroConfig:
        return self._get_location_section_or_default('pomodoro')

    def _get_location_section_or_default(self, section_name: str) -> Section:
        try:
            section_name = next((getattr(location, section_name) for location
                                 in self._config.locations if location.activation.start
                                 <= datetime.now().time() <= location.activation.end))
        except StopIteration:
            section_name = getattr(self._config, section_name)

        return section_name


class ConfigError(Exception):
    pass


class Singleton:
    _instance = None

    def __init__(self, init_instance: Callable, *args, **kwargs):
        self._init_instance = partial(init_instance, *args, **kwargs)

    def __getattr__(self, item: str) -> Any:
        try:
            return self._get_instance_attr(item)
        except AttributeError:
            Singleton._instance = self._init_instance()
            return self._get_instance_attr(item)

    @classmethod
    def _get_instance_attr(cls, item: str):
        return getattr(cls._instance, item)


def _create_config() -> Config:
    try:
        return Config(**load(CONFIG_PATH))
    except FileNotFoundError:
        return Config()


def get_config() -> Config:
    return cast(Config, Singleton(_create_config))


def get_client_config(client):
    return get_config().get('clients', {}).get(client, {})
