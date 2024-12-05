import logging
import os
import json
from dataclasses import dataclass


log_format = json.dumps({
    'timestamp': '%(asctime)s',
    'name': '%(name)s',
    'log_level': '%(levelname)s',
    'message': '%(message)s'
})
logging.basicConfig(
    format=log_format,
    level="INFO",
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)

logger = logging.getLogger()


def set_log_level(level: str):
    logger.setLevel(level)


@dataclass
class Config:
    discord_token: str
    log_level: str
    downloads_directory: str


def get_required_environment_variable(name: str) -> str:
    """Gets a required environment variable. Raises an error if it is not found or if it is an empty string"""
    value = os.getenv(name, None)
    if value is None or len(value.strip()) == 0:
        raise Exception(f"The environment variable `{name}` cannot be null or empty")

    return value


def get_environment_variable_with_default(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value


