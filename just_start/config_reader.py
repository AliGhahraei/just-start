from datetime import time, datetime
from os.path import join, expanduser, exists
from traceback import format_exc
from toml import load
from typing import Dict, Any

from .constants import CONFIG_PATH
from ._log import log


try:
    config = load(CONFIG_PATH)
except FileNotFoundError:
    log.warning(format_exc())
    config = {}


def get_client_config(client):
    return config.get('clients', {}).get(client, {})


class ConfigError(Exception):
    pass


def validate_config():
    value_errors = []
    for section_name, section_content in CONFIG_SECTIONS.items():
        try:
            validate_config_section(section_name, section_content)
        except ValueError as e:
            value_errors.append(f'{e} (in {section_name})')
    if value_errors:
        value_errors = '\n'.join([error for error in value_errors])
        raise ConfigError(f'Wrong configuration file:\n{value_errors}')


def validate_config_section(section_name: str, section_content: Dict) -> None:
    try:
        config[section_name]
    except KeyError:
        default_content = {name: content[0] for name, content
                           in section_content.items()}
        config[section_name] = default_content
    else:
        for field_name, field_content in section_content.items():
            default, validator = field_content
            try:
                config[section_name][field_name] = validator(
                    config[section_name][field_name])
            except KeyError:
                config[section_name][field_name] = default


def validate_type(object_: Any, type_: type) -> Any:
    if not isinstance(object_, type_):
        raise TypeError(f'Not a {type_.__name__}')
    return object_


def validate_positive_int(int_: Any) -> int:
    if validate_type(int_, int) < 1:
        raise ValueError(f'Non-positive integer: "{int_}"')
    return int_


def validate_list(list_: Any) -> list:
    return validate_type(list_, list)


def validate_bool(bool_: Any) -> bool:
    return validate_type(bool_, bool)


def validate_time(time_str: Any) -> time:
    return as_time(validate_str(time_str))


def validate_str(str_: Any) -> str:
    return validate_type(str_, str)


def as_time(time_str: str) -> time:
    return datetime.strptime(time_str, '%H:%M').time()


CONFIG_SECTIONS = {
    'general': {
        'password': ('', validate_str),
        'blocked_sites': ([], validate_list),
        'blocking_ip': ('127.0.0.1', validate_str),
        'taskrc_path': (expanduser(join('~')), validate_str),
    },
    'work': {
        'start': (as_time('09:00'), validate_time),
        'end': (as_time('18:00'), validate_time),
        'pomodoro_length': (25, validate_positive_int),
        'short_rest': (5, validate_positive_int),
        'long_rest': (15, validate_positive_int),
        'cycles_before_long_rest': (4, validate_positive_int),
    },
    'home': {
        'pomodoro_length': (25, validate_positive_int),
        'short_rest': (5, validate_positive_int),
        'long_rest': (15, validate_positive_int),
        'cycles_before_long_rest': (4, validate_positive_int),
    },
}

validate_config()
if not exists(expanduser(join(config['general']['taskrc_path'], '.taskrc'))):
    raise ConfigError(f'.taskrc could not be found in'
                      f' {config["general"]["taskrc_path"]}')
