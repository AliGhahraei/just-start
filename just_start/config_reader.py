from datetime import time, datetime
from os.path import expanduser
from typing import Dict, List, Generator, Callable, TypeVar

from pydantic import BaseModel, UrlStr, PositiveInt, FilePath, conint
from toml import load

from just_start.constants import CONFIG_PATH


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
    def __init__(self, config_path: str = CONFIG_PATH):
        self._loaded_config = None
        self.config_path = config_path
        self._at_work_override = False

    @property
    def read_config(self):
        return self._loaded_config if self._loaded_config is not None else self._load_config()

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

    def _load_config(self) -> _FullConfig:
        try:
            config = _FullConfig(**load(self.config_path))
        except FileNotFoundError:
            config = _FullConfig()

        self._loaded_config = config
        return self._loaded_config

    def _get_location_section_or_default(self, section_name: str) -> Section:
        try:
            section_name = next((getattr(location, section_name) for location
                                 in self.read_config.locations if location.activation.start
                                 <= datetime.now().time() <= location.activation.end))
        except StopIteration:
            section_name = getattr(self.read_config, section_name)

        return section_name


class ConfigError(Exception):
    pass


_config = _Config()


def get_general_config() -> GeneralConfig:
    return _config.general


def get_pomodoro_config() -> PomodoroConfig:
    return _config.pomodoro


def get_client_config(client: str) -> Dict[str, str]:
    return _config.clients.get(client, {})


def get_location_name() -> str:
    return _config.location_name
