from datetime import time, datetime
from os.path import expanduser
from typing import (
    Dict, List, Generator, Callable, TypeVar, cast,
)

from pydantic import BaseModel, UrlStr, PositiveInt, FilePath, conint
from toml import load

from just_start.constants import CONFIG_PATH
from just_start.singleton import Singleton


WeekdayInt = conint(le=0, ge=6)
ClientsConfig = Dict[str, Dict[str, str]]


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
    clients: ClientsConfig = {}


class _FullConfig(BaseModel):
    general: GeneralConfig = GeneralConfig()
    pomodoro: PomodoroConfig = PomodoroConfig()
    clients: ClientsConfig = {}
    locations: List[_LocationConfig] = []


Section = TypeVar('Section', bound=BaseModel)


class _Config:
    def __init__(self, **data):
        self._config = _FullConfig(**data)
        self._config_dict = self._config.dict()  # type: Dict
        self._at_work_override = False

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


def _load_config() -> _Config:
    try:
        return _Config(**load(CONFIG_PATH))
    except FileNotFoundError:
        return _Config()


class _ConfigSingleton(Singleton):
    pass


def _get_config() -> _Config:
    return cast(_Config, _ConfigSingleton(_load_config))


def get_general_config() -> GeneralConfig:
    return _get_config().general


def get_pomodoro_config() -> PomodoroConfig:
    return _get_config().pomodoro


def get_client_config(client: str) -> Dict[str, str]:
    return _get_config().clients.get(client, {})


def get_location_name() -> str:
    return _get_config().location_name
