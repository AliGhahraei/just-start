from collections.abc import MutableMapping
from datetime import time, datetime
from os.path import join, expanduser, exists
from traceback import format_exc
from typing import Dict, Any, Iterator

from json import load as json_load
from jsonschema import Draft4Validator, validators
from toml import load

from .constants import CONFIG_PATH, SCHEMA_PATH
from ._log import log


def as_time(time_str: str) -> time:
    return datetime.strptime(time_str, '%H:%M').time()


class Config(MutableMapping):
    def __init__(self, config_: Dict = None):
        self._at_work_override = False
        self._validate(config_)
        self._convert_types(config_)
        self._config = config_ or {}

    def __getitem__(self, key) -> Any:
        return self._config[key]

    def __setitem__(self, key, value) -> None:
        self._config[key] = value

    def __delitem__(self, value) -> None:
        del self._config[value]

    def __iter__(self) -> Iterator:
        return iter(self._config)

    def __len__(self) -> int:
        return len(self._config)

    @property
    def location(self):
        return self.work_location if self.at_work() else self._config

    @staticmethod
    def _validate(config: Dict):
        def extend_with_default(validator_class: Draft4Validator):
            validate_properties = validator_class.VALIDATORS["properties"]

            def set_defaults(validator, properties, instance, schema):
                for validator_property, subschema in properties.items():
                    if "default" in subschema:
                        instance.setdefault(validator_property, subschema["default"])

                for error in validate_properties(validator, properties, instance, schema):
                    yield error

            return validators.extend(validator_class, {"properties": set_defaults})

        default_validator = extend_with_default(Draft4Validator)
        with open(SCHEMA_PATH) as f:
            schema = json_load(f)
        default_validator(schema).validate(config)

    @staticmethod
    def _convert_types(config: Dict):
        for location in config['locations']:
            try:
                activation = location['activation']
            except KeyError:
                pass
            else:
                activation['start'] = as_time(activation['start'])
                activation['end'] = as_time(activation['end'])

    @property
    def work_location(self) -> Dict:
        return next((location for location in self._config['locations']
                     if location['name'] == 'work'))

    def at_work(self) -> bool:
        if self._at_work_override:
            return True

        return datetime.now().isoweekday() < 6 and (self.work_location['activation']['start']
                                                    <= datetime.now().time()
                                                    <= self.work_location['activation']['end'])


try:
    _original_config = load(CONFIG_PATH)
except FileNotFoundError:
    log.warning(format_exc())
    _original_config = dict()

config = Config(_original_config)


def get_client_config(client):
    return config.get('clients', {}).get(client, {})


class ConfigError(Exception):
    pass


def validate_config_section(section_name: str, section_content: Dict) -> None:
    try:
        config[section_name]
    except KeyError:
        default_content = {name: content[0] for name, content in section_content.items()}
        config[section_name] = default_content
    else:
        for field_name, field_content in section_content.items():
            default, validator = field_content
            try:
                config[section_name][field_name] = validator(config[section_name][field_name])
            except KeyError:
                config[section_name][field_name] = default


if not exists(expanduser(join(config['taskrc_path'], '.taskrc'))):
    raise ConfigError(f'.taskrc could not be found in'
                      f' {config["taskrc_path"]}')
