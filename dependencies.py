import configparser
from functools import lru_cache
from pydantic import ValidationError
from loguru import logger
from typing import Optional

from internal.controller import Client
from database import user_database, slice_database
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
def get_user_data_base() -> dict:
    return user_database


@lru_cache(1)
def get_slice_data_base() -> dict:
    return slice_database


@lru_cache(1)
def get_client() -> Optional[Client]:
    logger.info(f"Setting up gRPC Client")
    try:
        client = Client()
    except:
        logger.exception("Exception occured while setting up client!")
        return None
    client.get_base_info()
    # port_info = client.get_port_info()
    return client
