import json
from functools import lru_cache
from loguru import logger
from typing import Optional

from internal.controller import Client
from core.database import user_database, slice_database
from core.models import Configuration


@lru_cache(1)
def get_client(client_no: int = 0) -> Optional[Client]:
    config = get_config()
    logger.info(f"Setting up gRPC Client")
    try:
        client = Client(grpc_addr=config.grpc_urls[client_no])
    except:
        logger.exception("Exception occured while setting up client!")
        return None

    logger.debug(f"Connected with client {client_no}, dumping base_info")
    client.get_base_info()
    # port_info = client.get_port_info()
    return client

@lru_cache(1)
def get_base_model():
    client = get_client()
    base_model = client.bfrt_info.learn_get("digest_inst")
    base_model.info.data_field_annotation_add("src_addr", "ipv4")
    base_model.info.data_field_annotation_add("dst_addr", "ipv4")

@lru_cache(1)
def get_config() -> Configuration:
    with open("./config.json") as f:
        try:
            config = json.load(f)
            return Configuration(**config)
        except:
            logger.exception(f"Could not load config!")


@lru_cache(1)
def get_user_data_base() -> dict:
    return user_database


@lru_cache(1)
def get_slice_data_base() -> dict:
    return slice_database
