from collections import defaultdict
from datetime import time, datetime
from os.path import expanduser
from typing import (
    Dict, List, Generator, Callable, Any, Mapping, Iterator, TypeVar, cast, DefaultDict,
)

from pydantic import BaseModel, UrlStr, PositiveInt, FilePath, conint
from toml import load

from just_start.constants import CONFIG_PATH
from just_start.singleton import Singleton


WeekdayInt = conint(le=0, ge=6)
ClientsConfig = DefaultDict[str, Dict[str, str]]


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
    clients: ClientsConfig = defaultdict(dict)


class _FullConfig(BaseModel):
    general: GeneralConfig = GeneralConfig()
    pomodoro: PomodoroConfig = PomodoroConfig()
    clients: ClientsConfig = defaultdict(dict)
    locations: List[_LocationConfig] = []


Section = TypeVar('Section', bound=BaseModel)


class Config(Mapping):
    def __init__(self, **data):
        self._config = _FullConfig(**data)
        self._config_dict = self._config.dict()  # type: Dict
        self._at_work_override = False

    def __getitem__(self, item: str) -> Any:
        return getattr(self._config, item)

    def __iter__(self) -> Iterator[str]:
        return iter(self._config_dict)

    def __len__(self) -> int:
        return len(self._config_dict)

    @property
    def general(self) -> GeneralConfig:
        return self._get_location_section_or_default('general')

    @property
    def pomodoro(self) -> PomodoroConfig:
        return self._get_location_section_or_default('pomodoro')

    @property
    def clients(self) -> ClientsConfig:
        return self._get_location_section_or_default('clients')

    @property
    def location_name(self) -> str:
        return 'empty'

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


def _create_config() -> Config:
    try:
        return Config(**load(CONFIG_PATH))
    except FileNotFoundError:
        return Config()


class _ConfigSingleton(Singleton):
    pass


def get_config() -> Config:
    return cast(Config, _ConfigSingleton(_create_config))


def get_client_config(client: str) -> Dict[str, str]:
    return get_config().clients[client]
