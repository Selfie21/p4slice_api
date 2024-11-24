import configparser
from functools import lru_cache
from pydantic import ValidationError

from database import user_database
from models import Configuration

@lru_cache(1)
def get_config() -> Configuration:
    config = configparser.RawConfigParser()
    files_read = config.read("./.env")
    if files_read:
        default_section = dict(config["DEFAULT"].items())
        return Configuration(**default_section)
    else:
        FileNotFoundError("Config not found!")


@lru_cache(1)
def get_data_base() -> dict:
    return user_database
