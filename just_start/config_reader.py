from dataclasses import field
from datetime import time, datetime
from ipaddress import IPv4Address
from os.path import expanduser
from typing import Dict, List, TypeVar, Optional

from pydantic import PositiveInt, FilePath, conint, SecretStr
from pydantic.dataclasses import dataclass
from toml import load

from just_start.constants import CONFIG_PATH


ISOWeekday = conint(ge=1, le=7)
ConfigName = str
ClientsConfig = Dict[ConfigName, Dict[str, str]]


@dataclass
class _LocationActivationConfig:
    start: time
    end: time
    days: List[ISOWeekday]


@dataclass
class GeneralConfig:
    password: Optional[SecretStr] = None
    taskrc_path: FilePath = expanduser("~/.taskrc")
    blocked_sites: List[str] = field(default_factory=list)
    blocking_ip: IPv4Address = "127.0.0.1"
    notifications: bool = True


@dataclass
class PomodoroConfig:
    pomodoro_length: PositiveInt = 25
    short_rest: PositiveInt = 5
    long_rest: PositiveInt = 15
    cycles_before_long_rest: PositiveInt = 4


@dataclass
class _LocationConfig:
    name: str
    activation: _LocationActivationConfig
    general: GeneralConfig = field(default_factory=GeneralConfig)
    pomodoro: PomodoroConfig = field(default_factory=PomodoroConfig)
    clients: ClientsConfig = field(default_factory=dict)


@dataclass
class _FullConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    pomodoro: PomodoroConfig = field(default_factory=PomodoroConfig)
    clients: ClientsConfig = field(default_factory=list)
    locations: List[_LocationConfig] = field(default_factory=list)


Section = TypeVar('Section')


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
