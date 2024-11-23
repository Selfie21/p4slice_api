import configparser
from functools import lru_cache

from database import user_database


@lru_cache(1)
def get_config():
    config = configparser.RawConfigParser()
    files_read = config.read("./.env")
    if files_read:
        return config["DEFAULT"]
    else:
        FileNotFoundError("Config not found!")


@lru_cache(1)
def get_data_base():
    return user_database
